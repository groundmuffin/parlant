---
title: "Parlant 3.3: Scaling Control"
date: "March 15, 2026"
author: "Yam Marcovitz"
source: "https://www.parlant.io/blog/parlant-3-3-release"
---

[](https://www.linkedin.com/in/yam-marcovic/)[Yam Marcovitz](https://www.linkedin.com/in/yam-marcovic/)Parlant 3.3: Scaling ControlMarch 15, 20268 min readParlant has always been about control.


With 3.3, we're focused on what happens when your agent configuration grows, with more guidelines, more relationships, more tools, more edge cases.


The features in this release make it easier to manage complexity at scale, and to push behavioral control into places that were previously out of reach.


The headline changes are tag-based relationships for managing groups of guidelines as a unit, numeric priorities for explicit ordering without verbose relationship declarations, and transient guidelines that let tools dynamically inject behavioral instructions into the agent's context.


We've also added Agent.utter() for programmatic message generation in long-running background tasks, and made it significantly easier to update customer and session metadata from within tools.


Let's walk through the details!


Contents:


- Tag-Based RelationshipsTags as TargetsTag-Based Reevaluation
- Numeric PrioritiesPreventing Unguided Responses
- Transient Guidelines
- Agent.utter()
- Session and Customer MetadataSession MetadataCustomer Metadata
- Other Changes
- Getting Started
- In Summary



## Tag-Based Relationships​


As your agent grows, you can accumulate a large number of guidelines.


Managing individual relationships between them (this guideline excludes that one, this one depends on that one) can potentially become tedious and fragile. For example, when adding a new compliance guideline, you have to remember to wire up all the right exclusions.


Tags relationships are a new way to solve this.


In 3.3, tags become first-class participants in the relationship system. You can define dependencies, exclusions, priorities, and reevaluation relationships at the tag level, and every guideline carrying that tag inherits the relationship automatically.



#### Tags as Sources​


When you define a relationship on a tag, every guideline tagged with it gets the relationship:



```
compliance_guidelines = await server.create_tag("compliance-guidelines")redirect_off_topic = await agent.create_guideline(    condition="The customer is asking about topics outside our scope",    action="Redirect the conversation to our supported topics",    tags=[compliance_guidelines],)block_financial_advice = await agent.create_guideline(    condition="The customer asks for personal financial advice",    action="Explain that we cannot provide financial advice",    tags=[compliance_guidelines],)# All compliance guidelines take priority over casual conversationdiscussing_flights = await agent.create_observation(    "The customer is discussing flights")await compliance_guidelines.prioritize_over(discussing_flights)
```


Now every compliance guideline (both existing and future ones) automatically takes priority over the flight discussion guideline. When you add a new compliance rule, you can just tag it, without manually wiring relationships.



### Tags as Targets​


Tags also work as relationship targets, letting you define relationships against an entire group:



```
upsell_guidelines = await server.create_tag("upsell-guidelines")offer_seat_upgrade = await agent.create_guideline(    condition="The customer is booking a flight",    action="Offer a seat upgrade",    tags=[upsell_guidelines],)offer_lounge_access = await agent.create_guideline(    condition="The customer has a long layover",    action="Offer lounge access",    tags=[upsell_guidelines],)# When the customer is upset, suppress ALL upsell guidelines at oncecustomer_is_upset = await agent.create_observation(    "The customer is frustrated or upset")await customer_is_upset.exclude(upsell_guidelines)
```


One relationship declaration suppresses an entire category of behavior. This is the kind of thing that previously required N individual exclusions (one for each upsell guideline) and partially broke every time you added a new one.



### Tag-Based Reevaluation​


Tags also support reevaluation relationships with tools. When a tool fires, all guidelines carrying a tag with a reevaluation relationship to that tool are automatically re-evaluated:



```
balance_sensitive = await server.create_tag("balance-sensitive")await agent.create_guideline(    condition="The customer's balance is below $500",    action="Warn about potential overdraft fees",    tags=[balance_sensitive],)await agent.create_guideline(    condition="The customer's balance exceeds $10,000",    action="Suggest our premium savings account",    tags=[balance_sensitive],)# After checking the balance, re-evaluate all balance-sensitive guidelinesawait balance_sensitive.reevaluate_after(check_balance_tool)
```


Previously, you'd need to call reevaluate_after() on each individual guideline. With tag-based reevaluation, one declaration covers the whole group, and stays current as you add more guidelines to the tag.



## Numeric Priorities​


Relationships like prioritize_over() and depend_on() are powerful, but they're verbose when you need to express a clear ordering across many guidelines.


Parlant 3.3 introduces a numeric priority property on guidelines and journeys. Higher priority means higher precedence. When multiple guidelines are matched, only those at the highest priority level end up active for the next turn of the conversation.



```
await agent.create_guideline(    condition="Customer asks about pricing",    action="Quote standard pricing",    priority=0,  # Default priority is 0)await agent.create_guideline(    condition="Customer is an enterprise client",    action="Quote enterprise pricing with volume discounts",    priority=10,)await agent.create_guideline(    condition="Customer asks about a product under legal review",    action="Explain that pricing is temporarily unavailable",    priority=100,)
```


The relational resolver uses priority values during filtering: when conflicting guidelines are both matched, the lower-priority one is demoted. This works alongside explicit relationships — you can mix and match based on what's clearest for your configuration.


Priorities default to 0, so existing guidelines are unaffected. Journeys support the same property:



```
compliance_journey = await agent.create_journey(    name="Identity Verification",    priority=50,)
```



### Preventing Unguided Responses​


A clever trick that's made possible by priorities is the ability to prevent unguided responses from the agent.


By creating a catch-all guideline with a negative priority (lower than the default 0), you can ensure that the agent only responds when guidelines are active:



```
await agent.create_guideline(    matcher=p.MATCH_ALWAYS,    action="You must say you can't help them right now",    canned_responses=[        await server.create_canned_response("Sorry, I cannot help!"),    ],    composition_mode=p.CompositionMode.STRICT,    priority=-1,)
```



## Transient Guidelines​


Sometimes the right behavioral instruction doesn't exist at configuration time, like when a tool discovers, at runtime, how the agent should respond to a specific situation.


Transient guidelines let tools and retrievers inject behavioral guidelines into the agent's context dynamically. These guidelines are ephemeral: they apply only to the current response, then disappear. They don't persist in the session, and they don't affect future interactions.



```
@p.toolasync def check_order_status(    context: p.ToolContext,    order_id: str,) -> p.ToolResult:    order = await orders_api.get(order_id)    guidelines: list[p.TransientGuideline] = []    if order.status == "delayed":        guidelines.append({            "action": "Apologize for the delay",        })    if order.is_first_order:        guidelines.append({            "action": "Thank the customer for their first purchase",        })    return p.ToolResult(        data=order.to_dict(),        guidelines=guidelines,    )
```


The guidelines returned here are injected into the agent's context alongside the statically defined ones. They participate in priority filtering, support criticality levels, and can include descriptions, just like regular guidelines.


This is useful when you need to react to situations that are too dynamic to predefine


Transient guidelines are a natural extension of how tools already return canned responses and fields. They add another dimension: tools can now influence not just what data the agent sees, but how it should behave in response to that data.



## Agent.utter()​


Real-world agents often need to speak without an incoming customer message triggering them to do so. For example, your agent might follow up on a background operation (like a flight booking), notify a customer about an event, or check in after a period of inactivity.


Agent.utter() enables programmatic message generation. You provide a session and a set of transient guidelines, and the agent generates a contextually appropriate message:



```
# Invokedasync def follow_up_on_flight_booking(session: p.Session) -> None:    booking_id = await session.metadata.get("booking_id")    status = booking_api.check_status(booking_id)    if status == "confirmed":        await agent.utter(            session=session,            guidelines=[                {"action": "Confirm their flight has been booked."},            ],        )    else:        ...
```



## Session and Customer Metadata​


Managing session and customer state from within tools used to require working through the REST API. In 3.3, you can update metadata directly using the SDK's .current accessors.



### Session Metadata​



```
@p.toolasync def classify_inquiry(context: p.ToolContext) -> p.ToolResult:    session = p.Session.current    # Tag the session with metadata for analytics and routing    await session.metadata.set("topic", "billing")    await session.metadata.set("priority", "high")    return p.ToolResult(data="Inquiry classified")
```


You can also update the session's mode (for human handoff) and transfer it to a different agent:



```
# Switch to manual modeawait session.update(mode="manual")# Transfer to a specialistbilling_agent = await p.Server.current.get_agent(id="billing_specialist")await session.update(agent=billing_agent)
```



### Customer Metadata​


Similarly, tools can now update customer information directly:



```
@p.toolasync def update_customer_profile(    context: p.ToolContext,    new_location: str,) -> p.ToolResult:    customer = p.Customer.current    await customer.metadata.set("location", new_location)    return p.ToolResult(data="Profile updated")
```


This is especially useful for progressive profiling — building up customer context over the course of a conversation without leaving the tool execution scope.



## Other Changes​


SDK improvements:


- Server.get_tag() supports lookup by id or name
- reevaluate_after() now accepts multiple tools and returns Sequence[Relationship]
- tags field type changed from Sequence[TagId] to Sequence[Tag] across all entities


Bug fixes:


- Fixed deadlock when sending a message right after a preamble
- Fixed SSE read_event endpoint stalling after first streaming chunk
- Fixed response analysis logs not always reaching the integrated UI
- Fixed embedding LRU cache eviction corruption
- Fixed non-consequential tool calls being rejected when optional parameters are missing


Deprecations:


- OpenAPI tool services are now deprecated; please migrate to SDK tool services



## Getting Started​


Upgrade to Parlant 3.3:



```
pip install parlant --upgrade
```



## In Summary​


- Tag-based relationships let you manage behavior at the group level instead of wiring individual guidelines together.
- Numeric priorities give you explicit ordering without verbose relationship declarations.
- Transient guidelines let tools shape agent behavior at runtime, based on what they discover.
- Agent.utter() makes your agent proactive.
- Easier metadata management keeps your tools focused on business logic instead of API plumbing.


These features were shaped by feedback from teams running Parlant in production. As agents grow in complexity, the tools for managing that complexity need to grow with them. That's what 3.3 is about.


Questions? Join us on Discord or reach out via our contact page.


[Get in touch](https://discord.gg/duxWqxKk6J)Share post:[](https://www.linkedin.com/shareArticle?mini=true&url=https://www.parlant.io/blog/parlant-3-3-release/&text=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io)[](https://twitter.com/intent/tweet?url=https://www.parlant.io/blog/parlant-3-3-release/&text=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io)[](https://www.facebook.com/sharer/sharer.php?u=https://www.parlant.io/blog/parlant-3-3-release/)[](https://www.reddit.com/submit?url=https://www.parlant.io/blog/parlant-3-3-release/&title=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io)[](https://bsky.app/intent/compose?text=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io%20%20https%3A%2F%2Fwww.parlant.io%2Fblog%2Fparlant-3-3-release%2F)Tags:parlantreleasetagsrelationshipstransient-guidelines
