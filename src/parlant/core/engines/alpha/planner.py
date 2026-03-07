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
from dataclasses import dataclass

from parlant.core.agents import AgentId
from parlant.core.engines.alpha.engine_context import EngineContext


@dataclass(frozen=True)
class Plan:
    needs_additional_iteration: bool
    reasoning: str


class Planner(ABC):
    @abstractmethod
    async def plan(self, context: EngineContext) -> Plan:
        """Inspect the current engine context and decide what should run this iteration.

        The planner may mutate context.state (e.g. filtering tool_enabled_guideline_matches
        or ordinary_guideline_matches) to control which tools and guidelines are active
        for the current iteration. These fields are overwritten at the start of each
        subsequent iteration, so mutations are naturally scoped.

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


class PlannerProvider:
    """Provides planners on a per-agent basis."""

    def __init__(self, default_planner: Planner) -> None:
        self._default_planner = default_planner
        self._agent_planners: dict[AgentId, Planner] = {}

    def get_planner(self, agent_id: AgentId) -> Planner:
        return self._agent_planners.get(agent_id, self._default_planner)

    def set_planner(self, agent_id: AgentId, planner: Planner) -> None:
        self._agent_planners[agent_id] = planner
