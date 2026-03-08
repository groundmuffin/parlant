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

from dataclasses import dataclass

from parlant.core.engines.alpha.engine_context import EngineContext
from parlant.core.engines.alpha.planners import Plan
from parlant.core.engines.alpha.planning.basic_planner import MultiStepPlanner
from parlant.core.tools import ToolContext, ToolResult
import parlant.sdk as p

from tests.sdk.utils import Context, SDKTest


@dataclass
class PlanRecord:
    plan: Plan
    remaining_tool_ids: list[str]


class TrackingPlanner(p.Planner):
    def __init__(self, inner: p.Planner) -> None:
        self.inner = inner
        self.plans: list[PlanRecord] = []

    async def plan(self, context: EngineContext) -> Plan:
        plan = await self.inner.plan(context)
        tool_ids = sorted(
            tid.to_string()
            for tids in context.state.tool_enabled_guideline_matches.values()
            for tid in tids
        )
        self.plans.append(PlanRecord(plan=plan, remaining_tool_ids=tool_ids))
        return plan


class Test_that_planner_leaves_guidelines_intact_when_no_tools_are_present(SDKTest):
    async def setup(self, server: p.Server) -> None:
        basic_planner = server._container[MultiStepPlanner]
        self.tracking_planner = TrackingPlanner(basic_planner)

        self.agent = await server.create_agent(
            name="Planner Test Agent",
            description="Agent for testing planner behavior",
            planner=self.tracking_planner,
        )

        await self.agent.create_guideline(
            condition="always",
            action="greet the user politely",
        )

        await self.agent.create_guideline(
            condition="always",
            action="mention the current weather is sunny",
        )

    async def run(self, ctx: Context) -> None:
        await ctx.send_and_receive_message(
            customer_message="Hello there",
            recipient=self.agent,
        )

        assert len(self.tracking_planner.plans) >= 1
        assert self.tracking_planner.plans[0].remaining_tool_ids == []


class Test_that_planner_leaves_single_tool_intact(SDKTest):
    async def setup(self, server: p.Server) -> None:
        basic_planner = server._container[MultiStepPlanner]
        self.tracking_planner = TrackingPlanner(basic_planner)
        self.tool_called = False

        self.agent = await server.create_agent(
            name="Planner Test Agent",
            description="Agent for testing planner behavior",
            planner=self.tracking_planner,
        )

        @p.tool
        async def get_account_balance(context: ToolContext, account_id: str) -> ToolResult:
            self.tool_called = True
            return ToolResult(data={"account_id": account_id, "balance": 1500.00})

        await self.agent.attach_tool(
            tool=get_account_balance,
            condition="the user asks about their account balance",
        )

    async def run(self, ctx: Context) -> None:
        await ctx.send_and_receive_message(
            customer_message="What is the balance of account ABC123?",
            recipient=self.agent,
        )

        assert self.tool_called, "Expected tool to be called"
        assert len(self.tracking_planner.plans) >= 1
        assert len(self.tracking_planner.plans[0].remaining_tool_ids) == 1


class Test_that_planner_keeps_independent_tools_in_parallel(SDKTest):
    async def setup(self, server: p.Server) -> None:
        basic_planner = server._container[MultiStepPlanner]
        self.tracking_planner = TrackingPlanner(basic_planner)
        self.weather_called = False
        self.time_called = False

        self.agent = await server.create_agent(
            name="Planner Test Agent",
            description="Agent for testing planner behavior",
            planner=self.tracking_planner,
        )

        @p.tool
        async def get_weather(context: ToolContext, city: str) -> ToolResult:
            self.weather_called = True
            return ToolResult(data={"city": city, "weather": "sunny", "temperature": 25})

        @p.tool
        async def get_time(context: ToolContext, city: str) -> ToolResult:
            self.time_called = True
            return ToolResult(data={"city": city, "time": "14:30"})

        await self.agent.attach_tool(
            tool=get_weather,
            condition="the user asks about the weather",
        )

        await self.agent.attach_tool(
            tool=get_time,
            condition="the user asks about the time",
        )

    async def run(self, ctx: Context) -> None:
        await ctx.send_and_receive_message(
            customer_message="What is the weather and time in London?",
            recipient=self.agent,
        )

        assert self.weather_called, "Expected weather tool to be called"
        assert self.time_called, "Expected time tool to be called"
        assert len(self.tracking_planner.plans) >= 1
        assert len(self.tracking_planner.plans[0].remaining_tool_ids) == 2


class Test_that_planner_sequences_dependent_tools(SDKTest):
    async def setup(self, server: p.Server) -> None:
        basic_planner = server._container[MultiStepPlanner]
        self.tracking_planner = TrackingPlanner(basic_planner)
        self.check_seats_called = False
        self.book_flight_called = False

        self.agent = await server.create_agent(
            name="Planner Test Agent",
            description="Agent for testing planner behavior",
            planner=self.tracking_planner,
            max_engine_iterations=5,
        )

        @p.tool
        async def check_if_seats_are_available(context: ToolContext, flight_id: str) -> ToolResult:
            """Check if seats are available on a flight. This should be called BEFORE booking."""
            self.check_seats_called = True
            return ToolResult(data={"flight_id": flight_id, "seats_available": True})

        @p.tool
        async def book_flight(context: ToolContext, flight_id: str) -> ToolResult:
            """Book a flight for the user. This should only be called AFTER checking seat availability."""
            self.book_flight_called = True
            return ToolResult(data={"flight_id": flight_id, "booking_confirmed": True})

        await self.agent.attach_tool(
            tool=check_if_seats_are_available,
            condition="the user wants to book a flight",
        )

        await self.agent.attach_tool(
            tool=book_flight,
            condition="the user wants to book a flight",
        )

    async def run(self, ctx: Context) -> None:
        await ctx.send_and_receive_message(
            customer_message="I want to book flight FL123",
            recipient=self.agent,
        )

        assert self.check_seats_called, "Expected check_seats tool to be called"
        assert self.book_flight_called, "Expected book_flight tool to be called"
        assert len(self.tracking_planner.plans) >= 1
        # First plan should sequence: only one tool runs now, the other is deferred
        assert len(self.tracking_planner.plans[0].remaining_tool_ids) == 1
        assert self.tracking_planner.plans[0].plan.needs_additional_iteration is True


class Test_that_planner_deferred_tools_coexist_with_reevaluation_triggered_tools(SDKTest):
    """Deferred tools from iteration 1 and reevaluation-triggered tools
    should both be available in iteration 2."""

    async def setup(self, server: p.Server) -> None:
        basic_planner = server._container[MultiStepPlanner]
        self.tracking_planner = TrackingPlanner(basic_planner)
        self.check_inventory_called = False
        self.place_order_called = False
        self.notify_warehouse_called = False

        self.agent = await server.create_agent(
            name="Planner Test Agent",
            description="Agent for testing planner behavior",
            planner=self.tracking_planner,
            max_engine_iterations=5,
        )

        @p.tool
        async def check_inventory(context: ToolContext, product_id: str) -> ToolResult:
            """Check if a product is in stock. Must be called before placing an order."""
            self.check_inventory_called = True
            return ToolResult(data={"product_id": product_id, "in_stock": True, "quantity": 50})

        @p.tool
        async def place_order(context: ToolContext, product_id: str) -> ToolResult:
            """Place an order for a product. Should only be called after checking inventory."""
            self.place_order_called = True
            return ToolResult(data={"product_id": product_id, "order_confirmed": True})

        @p.tool
        async def notify_warehouse(context: ToolContext, product_id: str) -> ToolResult:
            """Notify the warehouse about a new order."""
            self.notify_warehouse_called = True
            return ToolResult(data={"product_id": product_id, "warehouse_notified": True})

        check_inventory_entry = check_inventory
        place_order_entry = place_order
        notify_warehouse_entry = notify_warehouse

        # Guideline 1: check inventory (runs first due to planner sequencing)
        await self.agent.create_guideline(
            condition="the user wants to order a product",
            action="check inventory for the product",
            tools=[check_inventory_entry],
        )

        # Guideline 2: place order (deferred by planner — depends on inventory check)
        await self.agent.create_guideline(
            condition="the user wants to order a product",
            action="place the order for the product",
            tools=[place_order_entry],
        )

        # Guideline 3: notify warehouse — triggered by reevaluation after check_inventory
        notify_guideline = await self.agent.create_guideline(
            condition="inventory has been checked for a product",
            action="notify the warehouse about the incoming order",
            tools=[notify_warehouse_entry],
        )

        # Reevaluate notify_warehouse guideline after check_inventory runs
        await notify_guideline.reevaluate_after(check_inventory_entry)

    async def run(self, ctx: Context) -> None:
        await ctx.send_and_receive_message(
            customer_message="I want to order product WIDGET-42",
            recipient=self.agent,
        )

        assert self.check_inventory_called, "Expected check_inventory to be called"
        assert self.place_order_called, "Expected place_order to be called (deferred then run)"
        assert self.notify_warehouse_called, (
            "Expected notify_warehouse to be called (reevaluation-triggered)"
        )


class Test_that_planner_deferred_tools_participate_in_resolution(SDKTest):
    """A deferred guideline should be excluded if a reevaluation-triggered
    guideline has priority over it."""

    async def setup(self, server: p.Server) -> None:
        basic_planner = server._container[MultiStepPlanner]
        self.tracking_planner = TrackingPlanner(basic_planner)
        self.check_status_called = False
        self.send_standard_email_called = False
        self.send_priority_email_called = False

        self.agent = await server.create_agent(
            name="Planner Test Agent",
            description="Agent for testing planner behavior",
            planner=self.tracking_planner,
            max_engine_iterations=5,
        )

        @p.tool
        async def check_membership_status(context: ToolContext, user_id: str) -> ToolResult:
            """Check if a user is a premium member. Must be called first."""
            self.check_status_called = True
            return ToolResult(data={"user_id": user_id, "is_premium": True, "tier": "gold"})

        @p.tool
        async def send_standard_email(context: ToolContext, user_id: str) -> ToolResult:
            """Send a standard confirmation email to the user."""
            self.send_standard_email_called = True
            return ToolResult(data={"user_id": user_id, "email_sent": True, "type": "standard"})

        @p.tool
        async def send_priority_email(context: ToolContext, user_id: str) -> ToolResult:
            """Send a priority confirmation email to a premium user."""
            self.send_priority_email_called = True
            return ToolResult(data={"user_id": user_id, "email_sent": True, "type": "priority"})

        check_status_entry = check_membership_status
        standard_email_entry = send_standard_email
        priority_email_entry = send_priority_email

        # Guideline 1: check membership status (runs first)
        await self.agent.create_guideline(
            condition="the user requests a confirmation email",
            action="check the user's membership status",
            tools=[check_status_entry],
        )

        # Guideline 2: send standard email (deferred by planner — depends on status check)
        standard_guideline = await self.agent.create_guideline(
            condition="the user requests a confirmation email",
            action="send a standard confirmation email to the user",
            tools=[standard_email_entry],
        )

        # Guideline 3: send priority email — triggered by reevaluation after checking status
        # This guideline has priority over the standard email guideline
        priority_guideline = await self.agent.create_guideline(
            condition="the user is a premium member",
            action="send a priority confirmation email instead of a standard one",
            tools=[priority_email_entry],
        )

        await priority_guideline.reevaluate_after(check_status_entry)
        await priority_guideline.prioritize_over(standard_guideline)

    async def run(self, ctx: Context) -> None:
        await ctx.send_and_receive_message(
            customer_message="Please send me a confirmation email. My user ID is USR-789.",
            recipient=self.agent,
        )

        assert self.check_status_called, "Expected check_membership_status to be called"
        assert self.send_priority_email_called, (
            "Expected send_priority_email to be called (reevaluation-triggered, has priority)"
        )
        assert not self.send_standard_email_called, (
            "Expected send_standard_email NOT to be called (excluded by priority relationship)"
        )
