---
title: "Parlant 3.0 — Reliable AI Agents"
date: "August 15, 2025"
author: "Yam Marcovitz"
source: "https://www.parlant.io/blog/parlant-3-0-release"
---

[](https://www.linkedin.com/in/yam-marcovic/)[Yam Marcovitz](https://www.linkedin.com/in/yam-marcovic/)Parlant 3.0 — Reliable AI AgentsAugust 15, 20257 min readToday we're thrilled to announce Parlant 3.0, our most significant release yet. This version transforms Parlant into a truly production-ready conversational AI framework for customer-facing applications. With dramatic performance improvements, enhanced developer experience, and enterprise-grade security features, Parlant 3.0 is ready to fix your hardest AI consistency issues and power your most critical customer-facing applications.



## What's New in Parlant 3.0​


This release focuses on four major areas that matter most to teams deploying conversational AI in production:


1. Latency Improvements & Perceived Performance - Dramatic speed improvements and responsive user experiences
2. Enhanced Journeys - More powerful conversation flows with state diagrams and tool integration
3. Canned Responses - New and improved (renamed from utterance templates), now supporting flexible composition modes
4. Production Readiness - API hardening, human handoff, custom NLP services, and extreme engine extensibility


Let's dive into each area in detail.



## Performance Improvements​


Performance is critical for conversational AI. Users expect a responsive experience, as freezes and extended delays can break the conversational flow. Parlant 3.0 introduces significant improvements in both actual and perceived performance.



### Optimized Response Generation Pipeline​


We've completely redesigned our response generation pipeline with several key optimizations:


- Parallel Processing: Journey state matching happens in parallel with guideline evaluation, reducing response latency by up to 60%
- Predictive Journey Activation: The engine predicts which journeys will be activated based on conversation context, allowing preemptive state preparation



### Perceived Performance with Preamble Responses​


Beyond raw speed improvements, Parlant 3.0 leverages perceived performance techniques. The most impactful addition is preamble responses:


![Preamble Response Example](https://www.parlant.io/img/blog-preamble-responses.png)


These instant acknowledgments keep users engaged while the agent processes complex requests in the background. The result is a conversational experience that feels immediate and responsive, even when performing complex operations.



## Enhanced Journeys: Guiding Complex Conversations​


Journeys in Parlant 3.0 have evolved into a sophisticated system for managing complex, multi-step conversations. They balance structure with flexibility, allowing agents to guide users through processes while remaining adaptive to natural conversation patterns.



### Journey Architecture Improvements​


Flexible State Transitions: Unlike rigid conversational frameworks, Parlant journeys allow agents to skip states, revisit previous states, or jump ahead based on context and user needs:



```
async def create_scheduling_journey(agent: p.Agent):    journey = await agent.create_journey(        title="Schedule Appointment",        description="Guides patients through appointment scheduling",        conditions=["The patient wants to schedule an appointment"]    )    # Create flexible state flow    t0 = await journey.initial_state.transition_to(        chat_state="Determine reason for visit"    )    t1 = await t0.target.transition_to(tool_state=get_upcoming_slots)    t2 = await t1.target.transition_to(        chat_state="Present available times"    )    # Conditional branching based on patient response    t3 = await t2.target.transition_to(        chat_state="Confirm appointment details",        condition="Patient selects a time"    )    # Alternative path for no suitable times    t4 = await t2.target.transition_to(        tool_state=get_later_slots,        condition="No suitable times available"    )    # ... additional states and transitions as needed    return journey
```



### Context-Aware Journey Management​


The engine dynamically manages which journeys are active based on conversation context, ensuring optimal performance and relevant responses:


- Dynamic Loading: Only relevant journeys are loaded into the LLM context
- Scoped Resources: Guidelines and canned responses can be scoped to specific journeys—even to specific states



## Canned Responses​


One of the biggest changes in Parlant 3.0 is the evolution from "utterance templates" to "Canned Responses" with flexible composition modes. This change reflects both improved functionality and clearer alignment with standard terminology.



### Three Composition Modes​


Parlant 3.0 introduces three distinct composition modes, each serving different use cases:



#### Fluid Mode​


The agent prioritizes canned responses when good matches exist, but falls back to natural generation otherwise.



```
await server.create_agent(    name="Support Agent",    description="Helpful customer support agent",    composition_mode=p.CompositionMode.FLUID)
```


Use Cases:​
- Prototyping agents while building response libraries
- Situations requiring mostly natural conversation with controlled responses for specific/sensitive responses



#### Composited Mode​


The agent uses canned response candidates to alter generated messages, mimicking their style and tone.



```
await server.create_agent(    name="Brand Agent",    description="Agent representing our brand voice",    composition_mode=p.CompositionMode.COMPOSITED)
```


Use Cases:​
- Brand-sensitive applications where tone consistency matters
- Maintaining voice and style guidelines across all responses



#### Strict Mode​


The agent can only output pre-approved canned responses. If no match exists, it sends a customizable no-match message.



```
await server.create_agent(    name="Compliance Agent",    description="Agent for highly regulated interactions",    composition_mode=p.CompositionMode.STRICT)
```


Use Cases:​
- High-risk environments that cannot tolerate hallucinations
- Regulated industries requiring pre-approved messaging
- Gradual UX improvement with tight control



### Advanced Response Features​


Dynamic Field Substitution:



```
await agent.create_canned_response(    template="Your current balance is {{account_balance}}")
```



```
# Tool provides dynamic fields@p.tooldef get_balance(context: p.ToolContext) -> p.ToolResult:    balance = fetch_balance(context.customer_id)    return p.ToolResult(        data=f"Balance: {balance}",        canned_response_fields={"account_balance": balance}    )
```


Generative Fields for controlled localization:



```
await agent.create_canned_response(    template="Sorry about the delay with {{generative.item_name}}")
```


Journey and State Scoping:



```
# Journey-scoped responsesawait journey.create_canned_response(    template="Let's continue with your appointment booking")
```



```
# State-specific responsesawait state.transition_to(    chat_state="Ask for preferences",    canned_responses=[        await server.create_canned_response(            template="What type of appointment do you need?"        )    ])
```



### No-Match Response Customization​


For strict mode deployments, Parlant 3.0 provides flexible no-match response handling:



```
# Static no-match responseasync def initialize_func(container: p.Container) -> None:    no_match_provider = container[p.BasicNoMatchResponseProvider]    no_match_provider.template = "Could you please rephrase that?"
```



```
# Dynamic no-match responsesclass CustomNoMatchProvider(p.NoMatchResponseProvider):    async def get_template(        self,        context: p.LoadedContext,        draft: str    ) -> str:        return generate_contextual_no_match_response(context, draft)
```


[Help with canned responses?](https://discord.gg/duxWqxKk6J)

## Production Readiness​


Parlant 3.0 finally transforms from a prototyping framework into a production-ready platform with comprehensive enterprise features.



#### API Hardening with Advanced Authorization​


Production deployments require robust security. Parlant 3.0 includes a complete API hardening system with fine-grained authorization and rate limiting.



#### Engine Extensibility with Dependency Injection​



```
async def configure_container(container: p.Container) -> p.Container:    container[p.AuthorizationPolicy] = CustomProductionAuthPolicy(        jwt_secret=os.environ["JWT_SECRET"],        jwt_algorithm="HS256",    )    return containerasync with p.Server(configure_container=configure_container) as server:    await server.serve()
```



#### Human Handoff Integration​


Real-world AI agents need seamless human escalation. Parlant 3.0 provides comprehensive human handoff capabilities:



#### Custom NLP Services​


Parlant 3.0 supports complete NLP service customization for specialized models or providers:



```
class CustomNLPService(p.NLPService):    async def get_schematic_generator(        self,        t: type[p.T]    ) -> p.SchematicGenerator[p.T]:        return CustomGenerator[p.T](model_config=self.config)    async def get_embedder(self) -> p.Embedder:        return CustomEmbedder(model_name="custom-embeddings-v2")    async def get_moderation_service(self) -> p.ModerationService:        return CustomModerationService(api_key=self.api_key)# Inject custom NLP serviceasync def load_nlp_service(container: p.Container) -> p.NLPService:    return CustomNLPService(logger=container[p.Logger])async with p.Server(nlp_service=load_nlp_service) as server:    # Agent behavior modeling code here
```



#### Engine Extensions and Hooks​


Parlant 3.0 provides comprehensive extension points, such as engine Hooks for response lifecycle customization:



```
async def validate_message_compliance(    ctx: p.LoadedContext, payload: Any, exc: Exception | None) -> p.EngineHookResult:    generated_message = payload    if not await is_compliant(generated_message):        ctx.logger.warning(            "Blocked non-compliant message: "            f"{generated_message}"        )        return p.EngineHookResult.BAIL    return p.EngineHookResult.CALL_NEXTasync def configure_hooks(hooks: p.EngineHooks) -> p.EngineHooks:    hooks.on_message_generated.append(validate_message_compliance)    return hooks
```


Completely customize or override core engine components:



```
async def configure_container(container: p.Container) -> p.Container:    # Replace any system component    container[p.MessageComposer] = CustomMessageComposer()    container[p.GuidelineMatcher] = OptimizedGuidelineMatcher()    return container
```


[Production-related questions?](https://discord.gg/duxWqxKk6J)

## Getting Started with Parlant 3.0​


Ready to try Parlant 3.0? Here's how to get started:



### Installation​



```
pip install parlant --upgrade
```



### Production Deployment​


For production deployments, check out our comprehensive documentation:


- API Hardening Guide - Secure your APIs with custom authorization
- Human Handoff Integration - Seamlessly escalate to human agents
- Custom NLP Services - Integrate your preferred models
- Engine Extensions - Customize core engine behavior



## What's Next​


Parlant 3.0 represents a major milestone in our mission to make conversational AI production-ready for everyone. But we're just getting started:


- Advanced Analytics - Comprehensive conversation analytics and insights with full OpenTelemetry integration
- Advanced Testing - Automated conversation testing and regression detection
- Compound Canned Responses — Assemble multiple canned responses into a single message
- Linked Journeys — Link multiple journeys together for complex workflows



Questions about Parlant 3.0? Join our Discord community or reach out directly to our team via our contact page.


[Get in touch!](https://discord.gg/duxWqxKk6J)Share post:[](https://www.linkedin.com/shareArticle?mini=true&url=https://www.parlant.io/blog/parlant-3-0-release/&text=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io)[](https://twitter.com/intent/tweet?url=https://www.parlant.io/blog/parlant-3-0-release/&text=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io)[](https://www.facebook.com/sharer/sharer.php?u=https://www.parlant.io/blog/parlant-3-0-release/)[](https://www.reddit.com/submit?url=https://www.parlant.io/blog/parlant-3-0-release/&title=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io)[](https://bsky.app/intent/compose?text=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io%20%20https%3A%2F%2Fwww.parlant.io%2Fblog%2Fparlant-3-0-release%2F)Tags:parlantai-agentsreleaseconversational-aiproductionperformance
