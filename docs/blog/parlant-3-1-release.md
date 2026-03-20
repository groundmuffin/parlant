---
title: "Parlant 3.1"
date: "January 1, 2026"
author: "Yam Marcovitz"
source: "https://www.parlant.io/blog/parlant-3-1-release"
---

[](https://www.linkedin.com/in/yam-marcovic/)[Yam Marcovitz](https://www.linkedin.com/in/yam-marcovic/)Parlant 3.1January 1, 202611 min readThe Emerging Power of Granular Behavior Control


Parlant has always been about control: giving you the ability to shape agent behavior precisely, reliably, and at scale.


Version 3.1 takes this further by adding granular control mechanisms across every layer of the framework.


This release introduces criticality levels for guidelines, custom matchers that let you override default matching logic, event handlers for guidelines and journey states, linked journeys for modular flow composition, dynamic composition mode overrides, and field providers that extend canned response capabilities.


Each of these features gives you finer control over how your agent behaves in specific situations.


Alongside these framework improvements, we're also launching Emcie, our first commercial offering: an auto-optimizing inference platform for teams looking to reduce operational costs while maintaining response accuracy.


We've worked closely with the community over the past 4 months to build on the foundation of version 3.0. Let's dive into the details.


Contents:


- Framework ImprovementsGuidelines and JourneysTools and RetrieversCanned ResponsesObservabilityManagement and Developer Workflow
- Getting Started with 3.1


[](https://www.emcie.co/)
As Parlant agents scale, there's a natural opportunity to optimize inference costs without compromising accuracy. Large language models deliver excellent results, but smaller models can often achieve comparable performance for specific, well-defined tasks once they're tuned for the job.


Incidentally, Parlant's architecture lends itself perfectly to SLM distillation, since each NLP task (guideline matching, tool calling, message generation) can be optimized independently.


We're super excited to introduce Emcie: our new auto-optimizing inference platform for Parlant agents. It automatically reduces operational costs through dynamic prompt tuning and SLM distillation, while maintaining the accuracy your agents need. Learn more at emcie.co.


With that, let's explore the key improvements in Parlant 3.1!



## Framework Improvements​



### Guidelines and Journeys​


Guidelines and journeys are central to how Parlant controls agent behavior. This release includes several improvements to both.



#### Linked Journeys​


You can now link journeys together by transitioning to another journey from within a state. This allows you to create modular, reusable journeys that compose into larger flows.



```
t = await state.transition_to(journey=payment_journey)
```



```
t = await state.transition_to(    condition="Customer wants to pay now",    journey=payment_journey,)
```


When you transition to a journey, the sub-journey's states are embedded into the parent journey. The transition returns a JourneyTransition whose .target is a fork state, letting you continue building the flow after the sub-journey completes.


This is useful for separating concerns: a checkout journey can link to a payment journey, which can link to a receipt journey, each maintained independently.



#### Journey Step Matching Efficiency​


Journey state matching is now 2x more efficient. This directly reduces latency for agents with complex multi-step flows.


The improvement comes from optimizations in how the engine evaluates transition conditions and predicts which states are likely to be active.



#### State and Guideline Descriptions​


Both journey states and guidelines now support a description field for elaboration. This is useful when a condition or action requires clarification, or when experimentation reveals that the agent isn't interpreting things correctly.



```
t = await state.transition_to(    chat_state="Confirm the booking details",    description="""At this point, summarize all collected information:destination, dates, number of travelers, and selected flight options.Ask the customer to verify everything is correct before proceeding.""")
```



```
await agent.create_guideline(    condition="The customer mentions a competitor product",    action="Acknowledge their experience and highlight our differentiators",    description="""Be respectful of competitor products while emphasizingour unique value. Never disparage competitors directly. Focus on featureslike our 24/7 support and flexible pricing.""")
```


The description is included in the agent's context when the guideline or state is active, improving both matching accuracy and the agent's ability to follow the instruction correctly.



#### Guideline Criticality​


As we expanded on in our recent blog post, not all instructions carry the same weight. A compliance disclosure has different stakes than a greeting preference. Parlant 3.1 introduces criticality levels that let you specify how much effort the engine should spend ensuring conformance.


LevelBehaviorUse CaseHIGHFull ARQ-based enforcement; maximum resources allocatedCompliance, legal obligations, safety-critical instructionsMEDIUMStandard enforcement with some flexibility (default)Core business logic, important but not criticalLOWTreated as subtle cues rather than rigid requirementsStylistic preferences, nice-to-have behavioral nudges

```
await agent.create_guideline(    condition="Customer asks about cancellation fees",    action="Disclose the $50 cancellation fee before proceeding",    criticality=p.Criticality.HIGH)await agent.create_guideline(    condition="The conversation has just started",    action="Inquire if they want to hear about on-sale items",    criticality=p.Criticality.LOW)
```


Low-criticality guidelines use a more efficient matching path, reducing compute costs for agents that make significant use of them. High-criticality guidelines always receive full ARQ-based matching and enforcement.



#### Match Handlers​


You can now register handlers that execute when a guideline or journey state is matched. This is useful for logging, analytics, or external integrations.


The on_match handler runs immediately after matching, before the agent generates its response:



```
async def log_match(ctx: p.EngineContext, m: p.GuidelineMatch) -> None:    await analytics.track("guideline_matched", {"id": m.id})await agent.create_guideline(    condition=CONDITION,    action=ACTION,    on_match=log_match,)
```


The on_message handler runs after the agent has generated and sent a message while the guideline was active:



```
await agent.create_guideline(    condition=CONDITION,    action=ACTION,    on_message=post_message_handler,)
```


Journey state transitions support the same handlers:



```
await state.transition_to(    chat_state=CHAT_STATE,    on_match=my_handler,    on_message=my_handler,)
```



#### Custom Matchers​


By default, Parlant uses LLM-based guideline matching. Custom matchers let you override this for specific guidelines.



```
async def my_matcher(    ctx: p.GuidelineMatchingContext,    guideline: p.Guideline) -> p.GuidelineMatch:    return p.GuidelineMatch(        id=guideline.id,        matched=True,        rationale="Custom logic determined this applies",    )await agent.create_guideline(    condition=CONDITION,    action=ACTION,    matcher=my_matcher,)
```


This enables several use cases:


Cost optimization: Match using simpler methods (embeddings, regex, smaller models) instead of LLM-based matching.


Always-on guidelines: For guidelines that should always be in context:



```
await agent.create_guideline(    condition="You need to present tabular data",    action="Use markdown table formatting",    matcher=p.MATCH_ALWAYS,  # Built-in helper)
```


Nuanced logic: Run specialized queries, consult external data sources, or apply complex business rules.



#### Subsequent Tool State Transitions​


Journeys now support transitioning through multiple consecutive tool states. This is useful for workflows that require several tool calls in sequence before presenting results to the customer.



### Tools and Retrievers​


Tool calling is one of the most latency-sensitive parts of the response pipeline. This release includes several optimizations.



#### Tool Consequentiality​


Tools can now be marked as consequential or non-consequential. Consequential tools have side effects that require careful evaluation before execution. Non-consequential tools are read-only or easily reversible.



```
@p.tool  # Non-consequential by defaultasync def get_order_status(    context: p.ToolContext, order_id: str) -> p.ToolResult:    status = await orders_api.get_status(order_id)    return p.ToolResult(data=status)@p.tool(consequential=True)async def process_refund(    context: p.ToolContext, order_id: str) -> p.ToolResult:    result = await payments_api.refund(order_id)    return p.ToolResult(data=result)
```


For non-consequential tools, Parlant optimizes for speed. Tools with no parameters run instantly without evaluation overhead. Tools with parameters use a faster evaluation path.


For consequential tools, Parlant applies full validation before execution.



#### Optimized Tool Evaluation​


We've restructured the tool evaluation pipeline to avoid unnecessary evaluation steps. In certain response cases, this saves up to 15 seconds of latency. The improvement is most noticeable for agents with many tools where only a subset applies to any given context.



#### Deferred Retrievers​


Retrievers typically run early in the pipeline, in parallel with guideline matching. This is optimal for latency, but sometimes you want to decide whether to include retriever results based on which guidelines actually matched.


Deferred retrievers solve this by returning a callable instead of a direct result:



```
async def conditional_retriever(    ctx: p.RetrieverContext) -> p.DeferredRetriever:    # Runs early, in parallel with guideline matching    documents = await fetch_documents(ctx.interaction.last_customer_message)    async def deferred(engine_ctx: p.EngineContext) -> p.RetrieverResult:        matched_ids = {g.id for g in engine_ctx.state.guidelines}        if MY_GUIDELINE_ID in matched_ids:            return p.RetrieverResult(data=documents)        return None  # Skip adding data    return deferredawait agent.attach_retriever(conditional_retriever)
```


This gives you parallel execution for the retrieval work while allowing context-aware filtering after guideline matching completes.



### Canned Responses​


Canned responses provide precise control over agent outputs, eliminating hallucination risk in high-stakes interactions. In Parlant 3.1, we've added several awesome enhancements.



#### Guideline and Journey State-Scoped Responses​


You can now associate canned responses directly with guidelines or journey states. These responses receive elevated consideration when the guideline is matched or the journey state is active.



```
await agent.create_guideline(    condition="Customer asks about refund policy",    action="Explain the refund policy",    canned_responses=[        await server.create_canned_response(            template="We offer full refunds within 30 days of purchase.",        ),    ])
```


The choice of creating them with the server or agent object matters: responses created via server are only considered when their associated guideline or state is active, while responses created via agent are always available but receive elevated priority when the association is active.



#### Dynamic Composition Mode​


While agents have a default composition mode (Fluid, Composited, or Strict), you can now override it temporarily based on active guidelines, journeys, or journey state transitions.



```
await agent.create_guideline(    condition="The customer is discussing off-topic subjects",    action="Explain you can only assist with account-related issues",    composition_mode=p.CompositionMode.STRICT,    canned_responses=[        await agent.create_canned_response(            template="I'm here to help with your account. Could we focus on that?"        ),    ])
```



```
t = await state.transition_to(    chat_state="Confirm payment details",    composition_mode=p.CompositionMode.STRICT,)
```


When multiple composition modes are active, the most restrictive wins: STRICT > COMPOSITED > FLUID. This lets you maintain a flexible agent overall while enforcing strict control in high-stakes situations.



#### Canned Response Metadata​


Canned responses can now include metadata that passes through to the frontend without being visible to the agent:



```
await agent.create_canned_response(    template="Here are your recommendations: {{recommendations}}",    metadata={        "reply_suggestions": [            "Tell me more",            "Show alternatives",            "Add to cart"        ],    },)
```


When this response is selected, the metadata is included in the response event, allowing your frontend to access it. This is useful for sending UI hints, reply suggestions, or other frontend-specific data alongside the response.



#### Field Providers for Guidelines and Journey States​


Guidelines and journey states can now provide fields for canned response templates, similar to how tools provide fields:



```
async def provide_discount_code(ctx: p.EngineContext) -> dict[str, Any]:    code = await generate_discount_code(ctx.customer.id)    return {"discount_code": code}await agent.create_guideline(    condition="Customer asks about available discounts",    action="Offer them a personalized discount",    canned_response_field_provider=provide_discount_code,)
```



```
await agent.create_canned_response(    template="Here's your discount code: {{discount_code}}")
```



### Observability​


Parlant 3.1 introduces built-in support for OpenTelemetry, the industry-standard framework for observability, with traces, metrics, and logs.



#### Backend Integration​


The OpenTelemetry integration works with any compatible backend: Jaeger, Grafana, Datadog, Honeycomb, and others. Each event in a session includes a trace_id field for correlating telemetry data with specific responses.



### Management and Developer Workflow​



#### Manual Entity ID Control​


You can now specify IDs when creating entities (agents, customers, sessions, etc.) rather than letting Parlant generate them.


For agents, this ensures consistent IDs across versions and changes.


For customers, this is useful for integrating with existing systems that have their own ID schemes.



#### Mid-Session Agent and Customer Changes​


Sessions now support changing the agent ID or customer ID mid-conversation. Use cases include:


- Escalation: Switching from a general support agent to a specialist agent
- Customer authentication: Starting with an anonymous session and associating a customer after authentication



#### FastAPI Configuration​


The configure_api hook gives you access to the underlying FastAPI instance. This allows adding custom endpoints, middleware, or other extensions for your deployment.



```
async def configure_api(app: FastAPI) -> None:    @app.get("/custom/health")    async def custom_health_check() -> dict[str, object]:        return {"status": "healthy", "custom": True}async with p.Server(configure_api=configure_api) as server:    await server.serve()
```



#### Health Endpoint​


A /healthz endpoint is now available for Kubernetes pod health monitoring and load balancer health checks.



#### Other Changes​


- Package manager: Switched from Poetry to uv for faster dependency resolution and installation
- Renamed context class: p.LoadedContext is now p.EngineContext. A deprecated alias exists for backward compatibility.



## Getting Started with 3.1​


Upgrade to Parlant 3.1:



```
pip install parlant --upgrade
```


For Emcie integration, set your API key and configure the NLP service:



```
export EMCIE_API_KEY="your-api-key"
```



```
async with p.Server(nlp_service=p.NLPServices.emcie) as server:    ...
```



#### In Summary​


Parlant 3.1 represents months of work informed by real-world production feedback. Many of the features in this release came directly from conversations with teams building agents at scale.


We're grateful to everyone who shared their experiences, reported issues, and contributed ideas.


If you're new to Parlant, there's never been a better time to get started. If you're already using it, we hope these improvements make your agents more capable and your development workflow smoother.


Questions? Join us on Discord or reach out via our contact page.


[Get in touch](https://discord.gg/duxWqxKk6J)Share post:[](https://www.linkedin.com/shareArticle?mini=true&url=https://www.parlant.io/blog/parlant-3-1-release/&text=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io)[](https://twitter.com/intent/tweet?url=https://www.parlant.io/blog/parlant-3-1-release/&text=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io)[](https://www.facebook.com/sharer/sharer.php?u=https://www.parlant.io/blog/parlant-3-1-release/)[](https://www.reddit.com/submit?url=https://www.parlant.io/blog/parlant-3-1-release/&title=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io)[](https://bsky.app/intent/compose?text=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io%20%20https%3A%2F%2Fwww.parlant.io%2Fblog%2Fparlant-3-1-release%2F)Tags:parlantreleasecontrolscale
