# Copyright 2026 Emcie Co Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import json
from typing import Any

from parlant.core.common import DefaultBaseModel
from parlant.core.engines.alpha.engine_context import EngineContext
from parlant.core.engines.alpha.guideline_matching.guideline_match import GuidelineMatch
from parlant.core.engines.alpha.planners import BasicPlanner, Plan
from parlant.core.engines.alpha.prompt_builder import PromptBuilder
from parlant.core.loggers import Logger
from parlant.core.nlp.generation import SchematicGenerator
from parlant.core.services.tools.service_registry import ServiceRegistry
from parlant.core.tracer import Tracer
from parlant.core.tools import (
    Tool,
    ToolContext,
    ToolId,
    ToolParameterDescriptor,
    ToolParameterOptions,
    ToolService,
)


class MultiStepPlanToolDecision(DefaultBaseModel):
    tool_id: str
    tldr: str
    should_run_now: bool


class MultiStepPlanSchema(DefaultBaseModel):
    analysis: str
    tool_decisions: list[MultiStepPlanToolDecision]


def _get_param_spec(descriptor: ToolParameterDescriptor, options: ToolParameterOptions) -> str:
    result: dict[str, Any] = {"schema": {"type": descriptor["type"]}}

    if descriptor["type"] == "array":
        result["schema"]["items"] = {"type": descriptor["item_type"]}

    if description := options.description:
        result["description"] = description
    elif description := descriptor.get("description"):
        result["description"] = description

    return json.dumps(result)


def _get_tool_spec(tool_id: ToolId, tool: Tool) -> dict[str, Any]:
    return {
        "tool_id": tool_id.to_string(),
        "name": tool.name,
        "description": tool.description,
        "parameters": {
            name: _get_param_spec(descriptor, options)
            for name, (descriptor, options) in tool.parameters.items()
        },
    }


class MultiStepPlanner(BasicPlanner):
    def __init__(
        self,
        schematic_generator: SchematicGenerator[MultiStepPlanSchema],
        service_registry: ServiceRegistry,
        logger: Logger,
        tracer: Tracer,
    ) -> None:
        super().__init__(logger=logger, tracer=tracer)
        self._schematic_generator = schematic_generator
        self._service_registry = service_registry

    async def do_plan(self, context: EngineContext) -> Plan:
        # Collect all unique ToolIds from tool_enabled_guideline_matches
        all_tool_ids: set[ToolId] = set()
        for tool_ids in context.state.tool_enabled_guideline_matches.values():
            for tid in tool_ids:
                all_tool_ids.add(tid)

        # If 0 or 1 tool, no planning needed
        if len(all_tool_ids) <= 1:
            self._logger.debug(
                f"Skipping planning: {len(all_tool_ids)} tool(s) found, no sequencing needed"
            )
            return Plan(
                needs_additional_iteration=False,
                reasoning="No planning needed since there is only one or zero tools to consider",
            )

        self._logger.debug(
            f"Planning for {len(all_tool_ids)} tools: "
            + ", ".join(tid.to_string() for tid in all_tool_ids)
        )

        # Resolve each ToolId to a Tool object
        tool_context = ToolContext(
            agent_id=context.agent.id,
            session_id=context.session.id,
            customer_id=context.customer.id,
        )

        services: dict[str, ToolService] = {}
        resolved_tools: dict[ToolId, Tool] = {}

        for tool_id in all_tool_ids:
            if tool_id.service_name not in services:
                services[tool_id.service_name] = await self._service_registry.read_tool_service(
                    tool_id.service_name
                )

            resolved_tools[tool_id] = await services[tool_id.service_name].resolve_tool(
                tool_id.tool_name, tool_context
            )

        # Build prompt
        builder = PromptBuilder()

        builder.add_agent_identity(context.agent)

        builder.add_section(
            name="planning_general_instructions",
            template="""GENERAL INSTRUCTIONS
-----------------
In our system, the behavior of an AI agent is guided by "guidelines". Each guideline is composed of a "condition" (when it applies) and an "action" (what the agent should do). Some guidelines have associated tools — external functions that the agent can call to retrieve information or perform actions.

The agent (you) processes each user's message in iterative steps. In each iteration, relevant guidelines are matched and their associated tools may be called. Tool results from one iteration are available in subsequent iterations, which allows for multi-step operations where later tools depend on earlier results.

You are a planning component within this system. You operate during each iteration, after the iteration's guidelines have been matched and their tools identified, but before any tool calls are made in this specific iteration. Your role is to decide which of the matched tools should execute in this iteration versus which should be deferred to a later iteration.

IMPORTANT: Note that you can see the previous iterations' tool calls and their results under "staged events".


Task Description
----------------
You are given a set of tools that have been identified as candidates for execution in the current iteration. Your task is to analyze dependencies between these tools and decide the execution order.

For each tool, decide whether it should run NOW or be DEFERRED:
- A tool should run NOW if it is independent, or if it gathers information that other tools need.
- A tool should be DEFERRED if it depends on the result of another tool that hasn't run yet, or if it should only execute after a precondition is verified by another tool.

When in doubt, prefer running tools now — only defer when there is a clear dependency or ordering requirement. If all tools are independent of each other, mark all of them to run now.

The exact format of your response will be provided later in this prompt.

""",
        )

        builder.add_customer_identity(context.customer, context.session)
        builder.add_interaction_history(context.interaction.events)
        builder.add_staged_tool_events(context.state.tool_events)

        # Tool descriptions
        tool_specs = [_get_tool_spec(tid, resolved_tools[tid]) for tid in all_tool_ids]

        builder.add_section(
            name="planning_tool_candidates",
            template="""Tool Candidates for Execution
-----------------
The following tools have been matched as candidates for this iteration. Analyze their descriptions and parameters to determine dependencies between them.

Tools: ###
{tool_specs}
###
""",
            props={"tool_specs": tool_specs},
        )

        builder.add_section(
            name="planning_output_format",
            template="""OUTPUT FORMAT
-----------------
Respond with a JSON object containing:
- "analysis": A brief analysis of the tool dependencies and execution ordering rationale
- "tool_decisions": A list of objects (one per tool), each with:
  - "tool_id": The tool ID string (exactly as listed above)
  - "tldr": Brief (TL;DR) explanation for the decision - short like a news headline
  - "should_run_now": true if the tool should execute in this iteration, false if it should be deferred
""",
        )

        # Call the schematic generator
        result = await self._schematic_generator.generate(builder)
        plan_schema = result.content

        self._logger.debug(f"Analysis: {plan_schema.analysis}")

        # Build a set of tool IDs that should run now
        tools_to_run_now: set[str] = set()
        tools_to_defer: set[str] = set()
        for decision in plan_schema.tool_decisions:
            if decision.should_run_now:
                tools_to_run_now.add(decision.tool_id)
                self._logger.debug(f"Run now: {decision.tool_id} ({decision.tldr})")
            else:
                tools_to_defer.add(decision.tool_id)
                self._logger.debug(f"Deferred: {decision.tool_id} ({decision.tldr})")

        # Filter context.state.tool_enabled_guideline_matches into
        # tools to run now vs. deferred to a later iteration.
        guidelines_to_move_to_ordinary: list[GuidelineMatch] = []
        updated_tool_enabled: dict[GuidelineMatch, list[ToolId]] = {}
        deferred_guideline_matches: dict[GuidelineMatch, list[ToolId]] = {}

        for guideline_match, tool_ids in context.state.tool_enabled_guideline_matches.items():
            kept_tools = [tid for tid in tool_ids if tid.to_string() in tools_to_run_now]
            deferred_tools = [tid for tid in tool_ids if tid.to_string() in tools_to_defer]

            if kept_tools:
                updated_tool_enabled[guideline_match] = kept_tools
            else:
                # All tools for this guideline are deferred
                guidelines_to_move_to_ordinary.append(guideline_match)

            if deferred_tools:
                deferred_guideline_matches[guideline_match] = deferred_tools

        context.state.tool_enabled_guideline_matches = updated_tool_enabled

        for gm in guidelines_to_move_to_ordinary:
            if gm not in context.state.ordinary_guideline_matches:
                context.state.ordinary_guideline_matches.append(gm)

        needs_additional = len(deferred_guideline_matches) > 0

        return Plan(
            needs_additional_iteration=needs_additional,
            reasoning=plan_schema.analysis,
            deferred_guideline_matches=deferred_guideline_matches,
        )
