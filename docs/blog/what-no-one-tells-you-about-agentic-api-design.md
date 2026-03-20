---
title: "Agentic Backends: What I Wish Someone Had Told Me About API Design for LLMs"
date: "July 15, 2025"
author: "Yam Marcovitz"
source: "https://www.parlant.io/blog/what-no-one-tells-you-about-agentic-api-design"
---

[](https://www.linkedin.com/in/yam-marcovic/)[Yam Marcovitz](https://www.linkedin.com/in/yam-marcovic/)Agentic Backends: What I Wish Someone Had Told Me About API Design for LLMsJuly 15, 202510 min readModern LLMs APIs have this powerful feature called "tool calling" or "function calling". Essentially, they can call API endpoints or functions to perform actions in the real world. Send an email, update a database, fetch weather data, etc.


Naturally, when developers discover this, their first reaction is: "Perfect! We already have an API. We'll just expose our existing endpoints as tools and let the LLM use them." This is seen as a quick and elegant way toward a conversational UI for your APIs.


Except it doesn't really work.



## The Core Issue​


While LLMs are essentially API consumers, they're fundamentally different from normal ones, which are... human developers. When an informed developer uses an API, they bring a lot of implicit knowledge to the table:


- Familiarity with your system's concepts and entities
- Understanding of the business logic and purpose
- Knowledge of the API's modularity and flow


But with LLMs, even if you feed them with some context, they're (comparatively) flying blind.


#mermaid-svg-2036573{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;fill:#000000;}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#mermaid-svg-2036573 .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#mermaid-svg-2036573 .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#mermaid-svg-2036573 .error-icon{fill:#552222;}#mermaid-svg-2036573 .error-text{fill:#552222;stroke:#552222;}#mermaid-svg-2036573 .edge-thickness-normal{stroke-width:1px;}#mermaid-svg-2036573 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-svg-2036573 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-svg-2036573 .edge-thickness-invisible{stroke-width:0;fill:none;}#mermaid-svg-2036573 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-svg-2036573 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-svg-2036573 .marker{fill:#666;stroke:#666;}#mermaid-svg-2036573 .marker.cross{stroke:#666;}#mermaid-svg-2036573 svg{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;}#mermaid-svg-2036573 p{margin:0;}#mermaid-svg-2036573 .edge{stroke-width:3;}#mermaid-svg-2036573 .section--1 rect,#mermaid-svg-2036573 .section--1 path,#mermaid-svg-2036573 .section--1 circle,#mermaid-svg-2036573 .section--1 polygon,#mermaid-svg-2036573 .section--1 path{fill:#555;}#mermaid-svg-2036573 .section--1 text{fill:#F4F4F4;}#mermaid-svg-2036573 .node-icon--1{font-size:40px;color:#F4F4F4;}#mermaid-svg-2036573 .section-edge--1{stroke:#555;}#mermaid-svg-2036573 .edge-depth--1{stroke-width:17;}#mermaid-svg-2036573 .section--1 line{stroke:#aaaaaa;stroke-width:3;}#mermaid-svg-2036573 .disabled,#mermaid-svg-2036573 .disabled circle,#mermaid-svg-2036573 .disabled text{fill:lightgray;}#mermaid-svg-2036573 .disabled text{fill:#efefef;}#mermaid-svg-2036573 .section-0 rect,#mermaid-svg-2036573 .section-0 path,#mermaid-svg-2036573 .section-0 circle,#mermaid-svg-2036573 .section-0 polygon,#mermaid-svg-2036573 .section-0 path{fill:#F4F4F4;}#mermaid-svg-2036573 .section-0 text{fill:#333;}#mermaid-svg-2036573 .node-icon-0{font-size:40px;color:#333;}#mermaid-svg-2036573 .section-edge-0{stroke:#F4F4F4;}#mermaid-svg-2036573 .edge-depth-0{stroke-width:14;}#mermaid-svg-2036573 .section-0 line{stroke:#0b0b0b;stroke-width:3;}#mermaid-svg-2036573 .disabled,#mermaid-svg-2036573 .disabled circle,#mermaid-svg-2036573 .disabled text{fill:lightgray;}#mermaid-svg-2036573 .disabled text{fill:#efefef;}#mermaid-svg-2036573 .section-1 rect,#mermaid-svg-2036573 .section-1 path,#mermaid-svg-2036573 .section-1 circle,#mermaid-svg-2036573 .section-1 polygon,#mermaid-svg-2036573 .section-1 path{fill:#555;}#mermaid-svg-2036573 .section-1 text{fill:#F4F4F4;}#mermaid-svg-2036573 .node-icon-1{font-size:40px;color:#F4F4F4;}#mermaid-svg-2036573 .section-edge-1{stroke:#555;}#mermaid-svg-2036573 .edge-depth-1{stroke-width:11;}#mermaid-svg-2036573 .section-1 line{stroke:#aaaaaa;stroke-width:3;}#mermaid-svg-2036573 .disabled,#mermaid-svg-2036573 .disabled circle,#mermaid-svg-2036573 .disabled text{fill:lightgray;}#mermaid-svg-2036573 .disabled text{fill:#efefef;}#mermaid-svg-2036573 .section-2 rect,#mermaid-svg-2036573 .section-2 path,#mermaid-svg-2036573 .section-2 circle,#mermaid-svg-2036573 .section-2 polygon,#mermaid-svg-2036573 .section-2 path{fill:#BBB;}#mermaid-svg-2036573 .section-2 text{fill:#333;}#mermaid-svg-2036573 .node-icon-2{font-size:40px;color:#333;}#mermaid-svg-2036573 .section-edge-2{stroke:#BBB;}#mermaid-svg-2036573 .edge-depth-2{stroke-width:8;}#mermaid-svg-2036573 .section-2 line{stroke:#444444;stroke-width:3;}#mermaid-svg-2036573 .disabled,#mermaid-svg-2036573 .disabled circle,#mermaid-svg-2036573 .disabled text{fill:lightgray;}#mermaid-svg-2036573 .disabled text{fill:#efefef;}#mermaid-svg-2036573 .section-3 rect,#mermaid-svg-2036573 .section-3 path,#mermaid-svg-2036573 .section-3 circle,#mermaid-svg-2036573 .section-3 polygon,#mermaid-svg-2036573 .section-3 path{fill:#777;}#mermaid-svg-2036573 .section-3 text{fill:#333;}#mermaid-svg-2036573 .node-icon-3{font-size:40px;color:#333;}#mermaid-svg-2036573 .section-edge-3{stroke:#777;}#mermaid-svg-2036573 .edge-depth-3{stroke-width:5;}#mermaid-svg-2036573 .section-3 line{stroke:#888888;stroke-width:3;}#mermaid-svg-2036573 .disabled,#mermaid-svg-2036573 .disabled circle,#mermaid-svg-2036573 .disabled text{fill:lightgray;}#mermaid-svg-2036573 .disabled text{fill:#efefef;}#mermaid-svg-2036573 .section-4 rect,#mermaid-svg-2036573 .section-4 path,#mermaid-svg-2036573 .section-4 circle,#mermaid-svg-2036573 .section-4 polygon,#mermaid-svg-2036573 .section-4 path{fill:#999;}#mermaid-svg-2036573 .section-4 text{fill:#333;}#mermaid-svg-2036573 .node-icon-4{font-size:40px;color:#333;}#mermaid-svg-2036573 .section-edge-4{stroke:#999;}#mermaid-svg-2036573 .edge-depth-4{stroke-width:2;}#mermaid-svg-2036573 .section-4 line{stroke:#666666;stroke-width:3;}#mermaid-svg-2036573 .disabled,#mermaid-svg-2036573 .disabled circle,#mermaid-svg-2036573 .disabled text{fill:lightgray;}#mermaid-svg-2036573 .disabled text{fill:#efefef;}#mermaid-svg-2036573 .section-5 rect,#mermaid-svg-2036573 .section-5 path,#mermaid-svg-2036573 .section-5 circle,#mermaid-svg-2036573 .section-5 polygon,#mermaid-svg-2036573 .section-5 path{fill:#DDD;}#mermaid-svg-2036573 .section-5 text{fill:#333;}#mermaid-svg-2036573 .node-icon-5{font-size:40px;color:#333;}#mermaid-svg-2036573 .section-edge-5{stroke:#DDD;}#mermaid-svg-2036573 .edge-depth-5{stroke-width:-1;}#mermaid-svg-2036573 .section-5 line{stroke:#222222;stroke-width:3;}#mermaid-svg-2036573 .disabled,#mermaid-svg-2036573 .disabled circle,#mermaid-svg-2036573 .disabled text{fill:lightgray;}#mermaid-svg-2036573 .disabled text{fill:#efefef;}#mermaid-svg-2036573 .section-6 rect,#mermaid-svg-2036573 .section-6 path,#mermaid-svg-2036573 .section-6 circle,#mermaid-svg-2036573 .section-6 polygon,#mermaid-svg-2036573 .section-6 path{fill:#FFF;}#mermaid-svg-2036573 .section-6 text{fill:#333;}#mermaid-svg-2036573 .node-icon-6{font-size:40px;color:#333;}#mermaid-svg-2036573 .section-edge-6{stroke:#FFF;}#mermaid-svg-2036573 .edge-depth-6{stroke-width:-4;}#mermaid-svg-2036573 .section-6 line{stroke:#000000;stroke-width:3;}#mermaid-svg-2036573 .disabled,#mermaid-svg-2036573 .disabled circle,#mermaid-svg-2036573 .disabled text{fill:lightgray;}#mermaid-svg-2036573 .disabled text{fill:#efefef;}#mermaid-svg-2036573 .section-7 rect,#mermaid-svg-2036573 .section-7 path,#mermaid-svg-2036573 .section-7 circle,#mermaid-svg-2036573 .section-7 polygon,#mermaid-svg-2036573 .section-7 path{fill:#DDD;}#mermaid-svg-2036573 .section-7 text{fill:#333;}#mermaid-svg-2036573 .node-icon-7{font-size:40px;color:#333;}#mermaid-svg-2036573 .section-edge-7{stroke:#DDD;}#mermaid-svg-2036573 .edge-depth-7{stroke-width:-7;}#mermaid-svg-2036573 .section-7 line{stroke:#222222;stroke-width:3;}#mermaid-svg-2036573 .disabled,#mermaid-svg-2036573 .disabled circle,#mermaid-svg-2036573 .disabled text{fill:lightgray;}#mermaid-svg-2036573 .disabled text{fill:#efefef;}#mermaid-svg-2036573 .section-8 rect,#mermaid-svg-2036573 .section-8 path,#mermaid-svg-2036573 .section-8 circle,#mermaid-svg-2036573 .section-8 polygon,#mermaid-svg-2036573 .section-8 path{fill:#BBB;}#mermaid-svg-2036573 .section-8 text{fill:#333;}#mermaid-svg-2036573 .node-icon-8{font-size:40px;color:#333;}#mermaid-svg-2036573 .section-edge-8{stroke:#BBB;}#mermaid-svg-2036573 .edge-depth-8{stroke-width:-10;}#mermaid-svg-2036573 .section-8 line{stroke:#444444;stroke-width:3;}#mermaid-svg-2036573 .disabled,#mermaid-svg-2036573 .disabled circle,#mermaid-svg-2036573 .disabled text{fill:lightgray;}#mermaid-svg-2036573 .disabled text{fill:#efefef;}#mermaid-svg-2036573 .section-9 rect,#mermaid-svg-2036573 .section-9 path,#mermaid-svg-2036573 .section-9 circle,#mermaid-svg-2036573 .section-9 polygon,#mermaid-svg-2036573 .section-9 path{fill:#999;}#mermaid-svg-2036573 .section-9 text{fill:#333;}#mermaid-svg-2036573 .node-icon-9{font-size:40px;color:#333;}#mermaid-svg-2036573 .section-edge-9{stroke:#999;}#mermaid-svg-2036573 .edge-depth-9{stroke-width:-13;}#mermaid-svg-2036573 .section-9 line{stroke:#666666;stroke-width:3;}#mermaid-svg-2036573 .disabled,#mermaid-svg-2036573 .disabled circle,#mermaid-svg-2036573 .disabled text{fill:lightgray;}#mermaid-svg-2036573 .disabled text{fill:#efefef;}#mermaid-svg-2036573 .section-10 rect,#mermaid-svg-2036573 .section-10 path,#mermaid-svg-2036573 .section-10 circle,#mermaid-svg-2036573 .section-10 polygon,#mermaid-svg-2036573 .section-10 path{fill:#777;}#mermaid-svg-2036573 .section-10 text{fill:#333;}#mermaid-svg-2036573 .node-icon-10{font-size:40px;color:#333;}#mermaid-svg-2036573 .section-edge-10{stroke:#777;}#mermaid-svg-2036573 .edge-depth-10{stroke-width:-16;}#mermaid-svg-2036573 .section-10 line{stroke:#888888;stroke-width:3;}#mermaid-svg-2036573 .disabled,#mermaid-svg-2036573 .disabled circle,#mermaid-svg-2036573 .disabled text{fill:lightgray;}#mermaid-svg-2036573 .disabled text{fill:#efefef;}#mermaid-svg-2036573 .section-root rect,#mermaid-svg-2036573 .section-root path,#mermaid-svg-2036573 .section-root circle,#mermaid-svg-2036573 .section-root polygon{fill:hsl(0, 0%, 70.6862745098%);}#mermaid-svg-2036573 .section-root text{fill:#333;}#mermaid-svg-2036573 .icon-container{height:100%;display:flex;justify-content:center;align-items:center;}#mermaid-svg-2036573 .edge{fill:none;}#mermaid-svg-2036573 .mindmap-node-label{dy:1em;alignment-baseline:middle;text-anchor:middle;dominant-baseline:middle;text-align:center;}#mermaid-svg-2036573 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}Successful API usageDeep API familiarityClear purposeError handlingStateful awarenessInput/output expectations
The problem is further amplified by the fact that LLMs are trained on billions of pages of human text like stories, conversations, and articles. So they're incredibly good at understanding natural language patterns. But APIs live in a different semantic universe. They contain numerous idiosyncracies that will trip up even the most sophisticated models.


Even more importantly, most APIs have zero tolerance for mistakes of even the smallest kind. It's not enough to be "semantically similar" when filling out a parameter. You have to follow a strict contract with absolute consistency.


Fred Brooks put it best in his classic book, The Mythical Man-Month: “If one character, one pause, of the incantation is not strictly in proper form, the magic doesn’t work [...] Adjusting to the requirement for perfection is, I think, the most difficult part of learning to program.”



### Modularity is a Double-Edged Sword​


Perhaps most critically, traditional APIs are modular by design. Want to send an email to a user? First, fetch the user's details. Then validate their email preferences. Finally, call the send endpoint. Each step has its own error states and success conditions.


For a human developer, this modularity is a crucial feature. For an LLM, it's literally begging for trouble.


We've consistently watched LLMs:


- Call step 3 without doing steps 1 and 2
- Repeat step 1 endlessly because they forgot they already did it
- Invent parameters for step 2 based on a creative interpretation of the function name
- Pass arguments that break the type system or violate the API contract
- Give up entirely and hallucinate a success response


LLMAPIHuman DeveloperLLMAPIHuman Developer#mermaid-svg-9550018{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;fill:#000000;}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#mermaid-svg-9550018 .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#mermaid-svg-9550018 .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#mermaid-svg-9550018 .error-icon{fill:#552222;}#mermaid-svg-9550018 .error-text{fill:#552222;stroke:#552222;}#mermaid-svg-9550018 .edge-thickness-normal{stroke-width:1px;}#mermaid-svg-9550018 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-svg-9550018 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-svg-9550018 .edge-thickness-invisible{stroke-width:0;fill:none;}#mermaid-svg-9550018 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-svg-9550018 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-svg-9550018 .marker{fill:#666;stroke:#666;}#mermaid-svg-9550018 .marker.cross{stroke:#666;}#mermaid-svg-9550018 svg{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;}#mermaid-svg-9550018 p{margin:0;}#mermaid-svg-9550018 .actor{stroke:hsl(0, 0%, 83%);fill:#eee;}#mermaid-svg-9550018 text.actor>tspan{fill:#333;stroke:none;}#mermaid-svg-9550018 .actor-line{stroke:hsl(0, 0%, 83%);}#mermaid-svg-9550018 .messageLine0{stroke-width:1.5;stroke-dasharray:none;stroke:#333;}#mermaid-svg-9550018 .messageLine1{stroke-width:1.5;stroke-dasharray:2,2;stroke:#333;}#mermaid-svg-9550018 #arrowhead path{fill:#333;stroke:#333;}#mermaid-svg-9550018 .sequenceNumber{fill:white;}#mermaid-svg-9550018 #sequencenumber{fill:#333;}#mermaid-svg-9550018 #crosshead path{fill:#333;stroke:#333;}#mermaid-svg-9550018 .messageText{fill:#333;stroke:none;}#mermaid-svg-9550018 .labelBox{stroke:hsl(0, 0%, 83%);fill:#eee;}#mermaid-svg-9550018 .labelText,#mermaid-svg-9550018 .labelText>tspan{fill:#333;stroke:none;}#mermaid-svg-9550018 .loopText,#mermaid-svg-9550018 .loopText>tspan{fill:#333;stroke:none;}#mermaid-svg-9550018 .loopLine{stroke-width:2px;stroke-dasharray:2,2;stroke:hsl(0, 0%, 83%);fill:hsl(0, 0%, 83%);}#mermaid-svg-9550018 .note{stroke:#999;fill:#666;}#mermaid-svg-9550018 .noteText,#mermaid-svg-9550018 .noteText>tspan{fill:#fff;stroke:none;}#mermaid-svg-9550018 .activation0{fill:#f4f4f4;stroke:#666;}#mermaid-svg-9550018 .activation1{fill:#f4f4f4;stroke:#666;}#mermaid-svg-9550018 .activation2{fill:#f4f4f4;stroke:#666;}#mermaid-svg-9550018 .actorPopupMenu{position:absolute;}#mermaid-svg-9550018 .actorPopupMenuPanel{position:absolute;fill:#eee;box-shadow:0px 8px 16px 0px rgba(0,0,0,0.2);filter:drop-shadow(3px 5px 2px rgb(0 0 0 / 0.4));}#mermaid-svg-9550018 .actor-man line{stroke:hsl(0, 0%, 83%);fill:#eee;}#mermaid-svg-9550018 .actor-man circle,#mermaid-svg-9550018 line{stroke:hsl(0, 0%, 83%);fill:#eee;stroke-width:2px;}#mermaid-svg-9550018 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}fetch_user_id(email)update_preferences(user_id)update_preferences(user_id) <!-- forgot fetch step -->

### Time for a Different Approach​


Many are working on making LLMs smarter about API interpretation and coding. This is a good step, but we need to do more. It's not enough to improve function-calling quality by another few percentage points.


We need to rethink how we design for LLMs. We need to understand that LLMs are a different type of API consumer with different needs, and design our APIs accordingly.


Essentially, what I'm suggesting is applying the pattern of BFF or Backend for Frontend, but to LLM (or agentic) frontends.


In other words, instead of creating a single API that categorically serves all consumers, we create a specialized API that is tailored to the unique needs of agentic frontends.


With that in mind, let's look at some of the most common failure modes and how to avoid them when designing APIs for LLMs.


[Get in touch with us](https://discord.gg/duxWqxKk6J)

## 1. Tools Need to Be Standalone​


Traditional API design embraces the principle of composability: small, reusable functions that work together. Need to update a user? First fetch their ID, then call the update endpoint.


But LLMs work best when they can match a clear user intent to a single action.


Consider these two API designs:


Traditional (Bad for Agents):



```
def get_user_id(email: str) -> int: ...def update_user_preferences(user_id: int, preferences: dict) -> bool: ...
```


Agent-Friendly (Good):



```
def update_user_preferences_by_email(email: str, preferences: dict) -> bool: ...
```



Agents struggle with multi-step workflows. Each tool call is a decision point where things can go wrong. The agent might:


- Forget to call get_user_id()
- Forget to store the intermediate result
- Misunderstand which ID to use if multiple are in context
- Hallucinate a user ID based on partial information
- Lose track of the overall goal between calls


Key Principle: Between "call the same function but parameterize it differently" and "create a standalone function for this particular context", try to heavily lean toward the latter. Think of a tool as a unique UI button instance.



### Avoiding Ambiguity​


A key observation here is that LLM APIs will naturally contain a lot of redundancy. This is not a bug, it's a feature. The more you can make each tool call self-contained, the less cognitive load you place on the agent, and the more robust your agentic API will be. See what I mean when I say we need to think differently about agentic APIs?


Additionally, tool functions will sometimes differ from each other in only minor ways. For example, schedule_appointment() and reschedule_appointment(). In a human context, these are clear. But for an agent, they can be confusing. This means that you should try to control, to the best of your ability, what tools you even allow your LLM agent to evaluate at any given time.


Incidentally, this is exactly why, in Parlant, tools must be associated with guidelines and can only run when the conditions for their associated guidelines are active.



## 2. Tools Should Be Idempotent​


Like I said before, LLMs will often call the same tool multiple times during a single interaction, either because they forgot they already did it or because they mistakenly think they need to do it again.


For example, they'll mistakenly call make_transaction() or send_email() multiple times, causing a mess. So if a customer comes in and says, "I want to send $50 to Bill", the agent then calls make_transaction(amount=50, recipient="Bill"). Then the customer says, "Thanks, so it's done, right?" and the agent calls it again, thinking it needs to confirm the transaction.


And there are even more trivial examples like just calling a tool again because the context still kind of "makes sense."


This is why you should design your tools to be idempotent. In other words, calling them multiple times with equivalent parameters (equivalent being an important word we'll circle back to) should yield the same result without side effects.


In Parlant, one of the tricks you can use to achieve this is to use the session ID as an idempotence key.




```
import parlant.sdk as p@p.tooldef make_transaction(    context: p.ToolContext,    amount: float,    recipient: str,) -> p.ToolResult:    global TRANSACTION_IDEMPOTENCE_TABLE    if context.session_id in TRANSACTION_IDEMPOTENCE_TABLE:        return p.ToolResult("Transaction already made in this session")    # Proceed with the transaction logic
```



The approach above is more simplistic and aggressive, essentially allowing only a single transaction per session. Of course, there are more nuanced ways
to approach it, but we'll leave it as an exercise for the reader.


[Get in touch with us](https://discord.gg/duxWqxKk6J)

## 3. Names Matter More Than You Think​


Quick: what's the difference between these functions?


- send_message()
- send_notification()
- send_email()
- send_alert()


To human developers reading docs it may be crystal clear, because they understand the API's terminology, and that each entity is a fundamentally different creature.


To an LLM it's a minefield. You won't believe how many false positives it'll have here.


Bad Design:



```
def send_notification(user_id: str, title: str, message: str): ...def send_message(recipient: str, content: str): ...
```


Good Design:



```
def send_email_to_user(email_address: str, subject: str, body: str):...def send_phone_sms_to_user(phone_number: str, text_content: str): ...
```


Be tediously explicit. Use names that:


- Include the key differentiator in the function name itself
- Clearly indicate what type of data is expected
- Avoid synonyms that might confuse
- Attract contextual attention with literal clues



## 4. Parameters Are Queries in Disguise​


With regular APIs, you can often assume the developer abided by the contract and passed the right data. For example, they won't pass an email for user_id if they can see that the API has a UserID entity that's returned by other endpoints. If they do, you just return an error. And once they see that their code is broken, they fix it. Then they ship it to production, and everything works.


But LLMs don't have that luxury, and they keep trying to figure out your API, from scratch, every single time. They won't code and debug it until it works, and only then ship it.


So if you don't want your agent to consistently fail at tool calls, you need to provide tool functions that are as tolerant as possible toward their arguments.


An effective design pattern here is to treat every parameter in your tool as essentially a query for that parameter's value. Sometimes the translation is direct, and sometimes it requires some inference.


Consider this function:



```
def schedule_meeting(participant_1, participant_2):
```


If each participant must follow a strict schema, such as email or valid user ID, then, for each parameter, the agent must:


1. Determine if it has this information
2. Extract it from context if available
3. Decide on a reasonable default if not
4. Format it correctly


That's 8 potential failure modes right there.


Instead, you can think of each parameter as a query. Something like this:




```
import parlant.sdk as p@p.tooldef schedule_meeting(    context: p.ToolContext,    participant_1: str | None = None,    participant_2: str | None = None,) -> p.ToolResult:    participants = [participant_1, participant_2]    if None in participants:        return p.ToolResult("Both participants must be provided")    actual_users = []    for p in participants:        user = None        # infer_type classifies with regex or perhaps even with NLP models        match infer_type(participant_1):            case "email":                user = find_user_by_email(p):            case "user_id":                user = find_user_by_user_id(p)            case "full_name":                user = find_user_by_full_name(p)            case _: pass        if user is None:            return p.ToolResult(f"Could not find user for {p}")    # Proceed with scheduling the meeting using actual_users
```



This will produce much more consistency in production.



## Agent-Friendly APIs​


These agent-friendly APIs are more verbose. They have more endpoints. They're more opinionated.


But we've learned that the cost of an agent misusing an API is far higher than the cost of a slightly larger API surface. One bad function call can derail an entire agent interaction, frustrating users and destroying trust.



### Practical Checklist for Agentic API Design​


Before releasing an API for agent consumption, ask yourself:


1. Can each tool facilitate a user's intent in a single, standalone call?
2. Would a non-technical person understand non-ambiguously what each tool does from its name alone?
3. Is each parameter name specific enough that misinterpretation is highly improbable?
4. Are your tools built to be idempotent, so they can be called multiple times without risky side effects?
5. Are you treating parameters as queries, allowing for flexible input without strict adherence to narrow contracts?



## Conclusion​


As AI agents become more prevalent, we need to evolve our API design philosophy. The principles that served us well for human-consumed APIs—flexibility, composability, abstraction—can actually become liabilities in the agentic world.


The good news is that LLMs are incredibly powerful and actually quite consistent when we design for their characteristics.


Have you encountered other surprising challenges in agentic API design? I'd love to hear about them.


[Get in touch with us](https://discord.gg/duxWqxKk6J)Share post:[](https://www.linkedin.com/shareArticle?mini=true&url=https://www.parlant.io/blog/what-no-one-tells-you-about-agentic-api-design/&text=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io)[](https://twitter.com/intent/tweet?url=https://www.parlant.io/blog/what-no-one-tells-you-about-agentic-api-design/&text=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io)[](https://www.facebook.com/sharer/sharer.php?u=https://www.parlant.io/blog/what-no-one-tells-you-about-agentic-api-design/)[](https://www.reddit.com/submit?url=https://www.parlant.io/blog/what-no-one-tells-you-about-agentic-api-design/&title=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io)[](https://bsky.app/intent/compose?text=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io%20%20https%3A%2F%2Fwww.parlant.io%2Fblog%2Fwhat-no-one-tells-you-about-agentic-api-design%2F)Tags:ai-agentsembeddingretrievalvector-databasevector-search
