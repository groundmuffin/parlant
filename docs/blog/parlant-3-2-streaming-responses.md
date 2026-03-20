---
title: "Parlant 3.2: Streaming Responses"
date: "February 8, 2026"
author: "Yam Marcovitz"
source: "https://www.parlant.io/blog/parlant-3-2-streaming-responses"
---

[](https://www.linkedin.com/in/yam-marcovic/)[Yam Marcovitz](https://www.linkedin.com/in/yam-marcovic/)Parlant 3.2: Streaming ResponsesFebruary 8, 202610 min readParlant has always been about control: giving you the ability to shape agent behavior precisely and reliably. Version 3.1 deepened that control with criticality levels, custom matchers, event handlers, and observability.


With 3.2, we've taken important steps to enhance user experience: not only in improving the UX itself, but also in making it easier to monitor and analyze your agent's interactions with your users.


We've heard from teams running Parlant in production that while behavioral accuracy is critical, perceived responsiveness and operational visibility matter just as much for adoption. This release is shaped by that feedback.


The headline change is streaming message output — responses that arrive token by token instead of as a single block. We've also added a built-in ability to categorize and track interaction sessions, along with deeper per-agent personality configuration, easier granular control of knowledge retrieval and context management, tighter control around canned response selection, and a collection of other fixes and improvements.


Let's walk through the details!


Contents:


- What Your Customers ExperienceStreaming ResponsesAgent Personality
- What You Can SeeLabels
- How You Tighten the ConfigurationControlling Reapplication with trackScoped Retrievers for Guidelines and JourneysField Dependencies for Canned ResponsesSDK Ergonomics
- Other Changes
- Getting Started
- In Summary



## What Your Customers Experience​


First, let's discuss the customer-facing improvements. Parlant 3.2 includes two major features that directly impact the user experience: streaming responses and enhanced agent personality configuration.



### Streaming Responses​


When a customer sends a message, your agent matches guidelines, calls tools, assembles context, and finally generates a response message.


Parlant goes through hoops to improve UX during the context assembly stage (with responsive status indicators and preamble messages), but the message generation part can also take a few seconds, and this has thus far remained unaddressed.


During message generation, the customer only saw a "typing" indicator.


For short replies, that's fine. But for agents that produce longer responses, the wait creates a gap that can feel unnatural.


The method of streaming (watching text appear word by word) often feels more responsive. It also lends itself better to voice agents, since the voice response can start generating and playing as soon as the first tokens are generated, rather than waiting for the full message to be ready.


Parlant 3.2's new streaming output mode finally closes this gap:



```
agent = await server.create_agent(    name="Support Agent",    description="Handles customer inquiries",    # New parameter to control response delivery    output_mode=p.OutputMode.STREAM,)
```


You configure the output mode per agent. We recommend streaming for customer-facing agents where perceived responsiveness matters.


infoWhen using canned responses, the agent will still revert to block output mode, even when streaming is enabled. This is useful when using dynamic composition mode, where only certain conditions trigger the use of canned responses, and the agent is left to operate in fluid mode for the rest of the time.



### Agent Personality​


Preambles are the quick acknowledgment messages — like "Got it" or "Let me check that" — that Parlant sends while processing a response, to keep the user engaged.


However, as different agents have different personalities, in 3.2, you can customize preamble behavior per agent, with concrete examples.



```
preamble_config = p.PreambleConfiguration(    examples=["Understood.", "Let me look into that.", "One moment."],)
```


You can also provide dynamic instructions to the preamble generator, so the preambles can adjust to the situation.



```
preamble_config = p.PreambleConfiguration(    examples=["Understood.", "Let me look into that.", "One moment."],    get_instructions=my_instruction_provider,)
```


The get_instructions callable receives an EngineContext, which gives you access to the current state of the session — matched guidelines, active journeys, customer information, and conversation history. You can use this to tailor the preamble generation to the situation at hand:



```
async def my_instruction_provider(ctx: p.EngineContext) -> Sequence[str]:    instructions = []    # Check the time of day for the customer    hour = datetime.now().hour    if hour < 12:        instructions.append("Use a morning greeting like 'Good morning'.")    elif hour >= 18:        instructions.append("Use an evening greeting like 'Good evening'.")    return instructions
```


This way, the same agent can adjust its preamble tone based on context — time-aware greetings, or any other signal you can derive from the session state.



## What You Can See​


With the customer experience addressed, let's turn to the developer's side.



### Labels​


One of the things that continues to surprise even ourselves about Parlant's architecture is how much you can build on top of Parlant's fundamental design decision: that guidelines and journeys are individual, well-defined units.


When you know exactly which instruction got activated and when, that opens doors you didn't plan for. Labels are a good example.


You can now set labels directly on guidelines, journeys, and journey states. Simple string tags. What does this enable?


Labels from these control primitives propagate into the session. Whenever a guideline matches, the session gets stamped with that guideline's labels. The same applies to journeys and journey states.


Over the course of a conversation, the session picks up relevant labels — giving you a record of what was activated and when.



```
await agent.create_guideline(    condition="The agent sees an opportunity to recommend a premium plan",    action="Suggest the premium plan and explain its benefits",    labels=["upsell_attempt"],)await agent.create_guideline(    condition="The customer is frustrated and wants to speak to a human",    action="Transfer the conversation to a human agent",    tools=[human_handoff],    labels=["human_handoff"],)
```


Now imagine you need to run analytics or filter sessions. With labels, you can pull up all sessions where an upsell was attempted, and examine them closely to understand how customers responded and optimize the interaction.


For example, if you have a human_handoff label, you can quickly surface every session where escalation occurred and investigate why.


And you can apply labels to journeys and states as well, not just guidelines.


Querying by labels is built into the client SDKs. For example, using parlant-client in TypeScript, you can filter sessions by one or more labels:



```
const upsellSessions = await client.sessions.list({    labels: ["upsell_attempt"],});
```


We expect labels to be useful for:


- Analytics and optimization: Which guidelines fire most? How do customers respond to upsell attempts?
- Routing: Route conversations to specialized agents or human teams based on accumulated labels.
- Filtering: Surface all sessions that touched a specific topic or triggered a specific flow.



## How You Tighten the Configuration​


Now that you can see what's happening and your customers are getting a better experience, the natural next step is refining the underlying mechanisms.


Parlant 3.2 adds improvements to guidelines, journeys, and canned responses.



### Controlling Reapplication with track​


As you may already know, Parlant, by default, tracks whether your agent has already applied a guideline's action and deactivates it to prevent repetition, even the condition is still met when looked at in its own right.


Usually, this is exactly what you want. You don't want the agent explaining the return policy five times in one conversation.


But not all actionable guidelines are one-time actions. Some are ongoing behavioral cues — tone adjustments, empathy responses, compliance reminders — that should apply every time their condition is met. For these, the default tracking may sometimes get in the way.


The new track parameter gives you explicit control on whether to enable it:



```
# Default: tracked, applies once per contextawait agent.create_guideline(    condition="Customer asks about pricing",    action="Provide current pricing",    track=True,  # default)# Untracked: reapplies every time the condition matchesawait agent.create_guideline(    condition="Customer expresses frustration",    action="Acknowledge their frustration and offer help",    track=False,)
```


Setting track=False bypasses the "previously applied" analysis entirely, so that your agent continually keeps this guideline in mind while the condition applies.



### Scoped Retrievers for Guidelines and Journeys​


In 3.1, retrievers were attached at the agent level and ran on every interaction. This works, but we found it leads to unnecessary context pollution in practice — pricing docs get retrieved during a password reset, troubleshooting articles load during a billing inquiry.


It was always possible to work around this using deferred retrievers, but it was something of an advanced usage pattern. So in 3.2, we've made this common pattern simpler to use.


You can now scope retrievers to specific guidelines or journeys. They only activate when the associated entity matches:



```
async def fetch_pricing_docs(ctx: p.RetrieverContext) -> p.RetrieverResult:    docs = await pricing_db.search(ctx.interaction.last_customer_message)    return p.RetrieverResult(data=docs)pricing_guideline = await agent.create_guideline(    condition="Customer asks about pricing",    action="Provide pricing based on their plan",)await pricing_guideline.attach_retriever(fetch_pricing_docs)
```


The same works for journeys and journey states: they all now support .attach_retriever().


The result is a cleaner context window and fewer wasted retriever calls. If the pricing guideline doesn't match, the pricing docs simply aren't fetched.


This approach trades some flexibility for precision. Agent-level retrievers remain the right choice when data is broadly useful across many guidelines. Scoped retrievers work best when data is clearly tied to a specific guideline or journey.



### Field Dependencies for Canned Responses​


Canned responses often reference dynamic data through template fields — {{order_status}}, {{delivery_date}}. Until now, there was no explicit way to express that a response requires those fields to be available, aside from actually referencing them in the response.


Field dependencies make this explicit, so you can condition the engine's selection of canned responses on the presence of specific fields in the context, even without your response referencing them directly:



```
await agent.create_canned_response(    template="Yay, your order is confirmed!",    field_dependencies=["new_order_id"],)
```


With this declaration, the engine only considers the response when both fields are available from an active tool or retriever. If the data isn't there, it filters the response out early.


This matters most in strict composition mode, where your agent must use a canned response. Field dependencies prevent the engine from selecting a response it can't fully render — and, consequently, from saying something it definitely shouldn't, like claiming something happened when it didn't.



### SDK Ergonomics​


A few smaller improvements that clean up common patterns:



#### Bulk relationship definitions​


prioritize_over() and depend_on() now accept multiple targets, so you can express a group of relationships in a single call:



```
await refund_guideline.prioritize_over(upsell_guideline, promo_guideline)await compliance_guideline.depend_on(identity_check, account_lookup)
```



#### Always-on guidelines​


Guideline conditions are now optional, so you can use a custom matcher without needing to provide a dummy condition:



```
await agent.create_guideline(    matcher=an_order_was_just_placed,,    action="Say 'Thank you for choosing Acme'",)
```



## Other Changes​


SDK improvements:


- Custom journey node IDs via the id parameter
- Matched guidelines and journey states included in the completion-ready event


Engine improvements:


- Tweaked default preamble examples for more natural tone
- Softened log levels for the relational guideline resolver
- Added activated/skipped logs to custom guideline matcher batches


Bug fixes:


- Fixed WebSocket warning on startup
- Fixed agent intention proposer incorrectly rewriting guidelines
- Fixed a bug with guideline/journey relationship resolution
- Fixed multiple custom guideline matchers not working together
- Fixed context variable access bug in SDK



## Getting Started​


Upgrade to Parlant 3.2:



```
pip install parlant --upgrade
```


To enable streaming on an existing agent:



```
await agent.update(output_mode=p.OutputMode.STREAM)
```



## In Summary​


Streaming responses and per-agent personality make your agent feel present. Labels give you visibility into what's actually happening across conversations. Scoped retrievers, field dependencies, and lifecycle hooks tighten the feedback loop between what you observe and what you configure.


Many of the features in this release came directly from conversations with teams building agents at scale. We're grateful to everyone who contributed feedback, reported issues, and shared their production experiences — this release is better because of it.


Questions? Join us on Discord or reach out via our contact page.


[Get in touch](https://discord.gg/duxWqxKk6J)Share post:[](https://www.linkedin.com/shareArticle?mini=true&url=https://www.parlant.io/blog/parlant-3-2-streaming-responses/&text=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io)[](https://twitter.com/intent/tweet?url=https://www.parlant.io/blog/parlant-3-2-streaming-responses/&text=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io)[](https://www.facebook.com/sharer/sharer.php?u=https://www.parlant.io/blog/parlant-3-2-streaming-responses/)[](https://www.reddit.com/submit?url=https://www.parlant.io/blog/parlant-3-2-streaming-responses/&title=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io)[](https://bsky.app/intent/compose?text=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io%20%20https%3A%2F%2Fwww.parlant.io%2Fblog%2Fparlant-3-2-streaming-responses%2F)Tags:parlantreleasestreaminglabels
