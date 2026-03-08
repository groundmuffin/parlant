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

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from parlant.core.agents import AgentId
from parlant.core.engines.alpha.engine_context import EngineContext
from parlant.core.engines.alpha.guideline_matching.guideline_match import GuidelineMatch
from parlant.core.loggers import Logger
from parlant.core.tools import ToolId
from parlant.core.tracer import Tracer

_PLANNER_SPAN_NAME = "planner"


@dataclass(frozen=True)
class Plan:
    needs_additional_iteration: bool
    reasoning: str
    deferred_guideline_matches: dict[GuidelineMatch, list[ToolId]] = field(default_factory=dict)
    """Guidelines whose tools were deferred to a later iteration.

    The engine will re-inject these into the next iteration's resolution step,
    so they participate in relational resolution (priority, dependency, etc.)
    alongside any newly reevaluated guidelines. The planner will then see them
    again and can decide whether to run or further defer them.
    """


class Planner(ABC):
    @abstractmethod
    async def plan(self, context: EngineContext) -> Plan:
        """Inspect the current engine context and decide what should run this iteration.

        The planner may mutate context.state (e.g. filtering tool_enabled_guideline_matches
        or ordinary_guideline_matches) to control which tools and guidelines are active
        for the current iteration. These fields are overwritten at the start of each
        subsequent iteration, so mutations are naturally scoped.

        To defer tools to a later iteration, populate Plan.deferred_guideline_matches.
        The engine will re-inject deferred guidelines into the next iteration's
        resolution step, where they participate in relational resolution alongside
        any newly reevaluated guidelines.

        Returns a Plan indicating whether an additional iteration is needed
        (beyond what reevaluation relationships would trigger) and optional reasoning
        for observability.
        """
        ...


class NullPlanner(Planner):
    async def plan(self, context: EngineContext) -> Plan:
        return Plan(
            needs_additional_iteration=False,
            reasoning="",
        )


class BasicPlanner(Planner):
    """Base planner with built-in tracing and logger scoping.

    Derived classes implement do_plan() instead of plan().
    """

    def __init__(self, logger: Logger, tracer: Tracer) -> None:
        self._logger = logger
        self._tracer = tracer

    @abstractmethod
    async def do_plan(self, context: EngineContext) -> Plan: ...

    async def plan(self, context: EngineContext) -> Plan:
        with self._logger.scope(type(self).__name__):
            with self._tracer.span(_PLANNER_SPAN_NAME):
                return await self.do_plan(context)


class PlannerProvider:
    """Provides planners on a per-agent basis."""

    def __init__(self, default_planner: Planner) -> None:
        self._default_planner = default_planner
        self._agent_planners: dict[AgentId, Planner] = {}

    def get_planner(self, agent_id: AgentId) -> Planner:
        return self._agent_planners.get(agent_id, self._default_planner)

    def set_planner(self, agent_id: AgentId, planner: Planner) -> None:
        self._agent_planners[agent_id] = planner
