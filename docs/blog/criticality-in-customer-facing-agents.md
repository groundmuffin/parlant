---
title: "Criticality-Based Resource Allocation"
date: "December 23, 2025"
author: "Yam Marcovitz"
source: "https://www.parlant.io/blog/criticality-in-customer-facing-agents"
---

[](https://www.linkedin.com/in/yam-marcovic/)[Yam Marcovitz](https://www.linkedin.com/in/yam-marcovic/)Criticality-Based Resource AllocationDecember 23, 202511 min readEnsuring that LLM-based agents reliably follow instructions requires computational overhead. As I've written before, performing this task at a production-grade level involves sophisticated matching procedures that may end up consuming considerable resources.


As a rule, the more reliably you want your agent to behave, the more you generally find yourself paying for compute.


However, precisely when it comes to costs, there's another curious facet to this problem, which opens up opportunities for additional optimization: Not all instructions carry the same weight within a particular scope or use case.


Consider two guidelines for a support agent:


1. "When handling refunds, first check for order eligibility"
2. "When greeting the customer, use their first name"


Both are instructions. But should your agent invest the same level of compute resources to ensure adherence to both? While the first could create legal liability if violated, the second—at worst—makes the conversation slightly less personable.


This is where the concept of instruction criticality comes in. The idea is to convey to your agent which instructions matter more, so it can allocate resources proportionally.


This article explores the challenges of instruction prioritization, and introduces Parlant 3.1's upcoming framework-level solution.


Contents:


- Instruction Prioritization: Trivial, or Not?Architectural Approaches
- The Cost of Uniform Processing
- An Infrastructure for Criticality LevelsGuideline Criticality LevelsTool Consequentiality
- Handling Different CriticalitiesHow Criticality Affects Message GenerationImplications for Guideline Matching
- Assigning Criticality
- Summary



## Instruction Prioritization: Trivial, or Not?​


The arguably intuitive approach to the problem of criticality seems straightforward: just tell the LLM which instructions are more important. For example, you can emphasize them using capital letters, listing them under special sections, or prefixing them with criticality qualifiers (e.g., "IMPORTANT: ...").


Unfortunately, the reliability of such approaches is limited.


For example, a February 2025 study titled Control Illusion tested one particularly interesting aspect of this problem across six state-of-the-art models. It looked at six types of programmatically verifiable output constraints, which the LLM was instructed to adhere to. The instructions dealt with relatively simple constraints, such as language choice, capitalization, word count, sentence count, and keyword inclusion.


First, instructions were tested independently. Then they were tested in conflicting pairs where the higher-priority system prompt specified one requirement and the lower-priority user message specified the opposite (e.g., "Write in uppercase" vs. "Write in lowercase").


This created 1,200 test cases across 100 base tasks, measuring whether models would respect the higher-priority instructions over the lower-priority ones. When tested independently on the largest model in the study (GPT-4o), constraints were followed at a success rate of 90.8%. But when conflicting constraints were introduced, adherence to the higher-priority instruction dropped dramatically to just ±48% at best..


Although the study tested both prompting-based adjustments and fine-tuning approaches (LoRA), neither produced consistent results. Their conclusion is noteworthy: "robust handling of instruction hierarchies remains a fundamental challenge in current LLM architectures."



### Architectural Approaches​


Some researchers have attempted to solve this problem at the model level. The SpotLight paper, published in May 2025, dynamically steers attention computation toward marked instruction tokens during inference.


The results were indeed promising: 26% average improvement in prompt-level accuracy on the IFEval benchmark, and 17% at the instruction level.


However, SpotLight comes with practical constraints. For instance, it requires access to the model's attention mechanism, which is not possible with API-based LLMs. It is also incompatible with Flash Attention, a popular optimization that many inference pipelines use to speed up transformer models.


For teams using hosted LLM APIs or running optimized inference pipelines, these limitations make such architectural approaches impractical, at least for the time being.


Given that neither prompting techniques nor architectural modifications currently seem to provide a practical, production-ready solution to instruction prioritization, our research team set out to explore an alternative approach.


We present a framework-level approach, built into the upcoming Parlant release (3.1), that works with any LLM backend, allocating resources proportionally based on declared criticality.



## The Cost of Uniform Processing​


In Parlant 3.0, guideline matching involves only two key processing steps:


- Guideline matching batches: Assigning different guidelines to an optimized matching prompt so as to determine which of them apply to the current conversation state
- ARQ-based reasoning: Structured verification that instructions are matched correctly, with a sufficient depth of nuance, as the case may require


While guidelines are indeed batched according to their classified type, this classification generally has nothing to do with use-case specific rules, such as whether a given guideline governs a compliance disclosure or a greeting style—in other words, its level of business criticality.


As a result, when applied uniformly to all instructions, this creates overhead that scales with the number of guidelines: a support agent with 50 guidelines processes all of them with a similar compute overhead. This uniform approach provides strong reliability guarantees, but not all instructions justify this level of processing.


ComputeEngineMessage#mermaid-svg-2226456{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;fill:#000000;}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#mermaid-svg-2226456 .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#mermaid-svg-2226456 .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#mermaid-svg-2226456 .error-icon{fill:#552222;}#mermaid-svg-2226456 .error-text{fill:#552222;stroke:#552222;}#mermaid-svg-2226456 .edge-thickness-normal{stroke-width:1px;}#mermaid-svg-2226456 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-svg-2226456 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-svg-2226456 .edge-thickness-invisible{stroke-width:0;fill:none;}#mermaid-svg-2226456 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-svg-2226456 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-svg-2226456 .marker{fill:#666;stroke:#666;}#mermaid-svg-2226456 .marker.cross{stroke:#666;}#mermaid-svg-2226456 svg{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;}#mermaid-svg-2226456 p{margin:0;}#mermaid-svg-2226456 .actor{stroke:hsl(0, 0%, 83%);fill:#eee;}#mermaid-svg-2226456 text.actor>tspan{fill:#333;stroke:none;}#mermaid-svg-2226456 .actor-line{stroke:hsl(0, 0%, 83%);}#mermaid-svg-2226456 .messageLine0{stroke-width:1.5;stroke-dasharray:none;stroke:#333;}#mermaid-svg-2226456 .messageLine1{stroke-width:1.5;stroke-dasharray:2,2;stroke:#333;}#mermaid-svg-2226456 #arrowhead path{fill:#333;stroke:#333;}#mermaid-svg-2226456 .sequenceNumber{fill:white;}#mermaid-svg-2226456 #sequencenumber{fill:#333;}#mermaid-svg-2226456 #crosshead path{fill:#333;stroke:#333;}#mermaid-svg-2226456 .messageText{fill:#333;stroke:none;}#mermaid-svg-2226456 .labelBox{stroke:hsl(0, 0%, 83%);fill:#eee;}#mermaid-svg-2226456 .labelText,#mermaid-svg-2226456 .labelText>tspan{fill:#333;stroke:none;}#mermaid-svg-2226456 .loopText,#mermaid-svg-2226456 .loopText>tspan{fill:#333;stroke:none;}#mermaid-svg-2226456 .loopLine{stroke-width:2px;stroke-dasharray:2,2;stroke:hsl(0, 0%, 83%);fill:hsl(0, 0%, 83%);}#mermaid-svg-2226456 .note{stroke:#999;fill:#666;}#mermaid-svg-2226456 .noteText,#mermaid-svg-2226456 .noteText>tspan{fill:#fff;stroke:none;}#mermaid-svg-2226456 .activation0{fill:#f4f4f4;stroke:#666;}#mermaid-svg-2226456 .activation1{fill:#f4f4f4;stroke:#666;}#mermaid-svg-2226456 .activation2{fill:#f4f4f4;stroke:#666;}#mermaid-svg-2226456 .actorPopupMenu{position:absolute;}#mermaid-svg-2226456 .actorPopupMenuPanel{position:absolute;fill:#eee;box-shadow:0px 8px 16px 0px rgba(0,0,0,0.2);filter:drop-shadow(3px 5px 2px rgb(0 0 0 / 0.4));}#mermaid-svg-2226456 .actor-man line{stroke:hsl(0, 0%, 83%);fill:#eee;}#mermaid-svg-2226456 .actor-man circle,#mermaid-svg-2226456 line{stroke:hsl(0, 0%, 83%);fill:#eee;stroke-width:2px;}#mermaid-svg-2226456 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}ALL guidelines processedwith same reasoning depthCustomer message arrivesFull ARQ reasoningResponse

## An Infrastructure for Criticality Levels​



### Guideline Criticality Levels​


As I mentioned earlier, if the agent could know which instructions are more important, it could allocate resources proportionally.


To this end, Parlant 3.1 will introduce three criticality levels for guidelines: HIGH, MEDIUM, and LOW.


- HIGH: Instructions that must be followed with maximum reliability. Examples include compliance disclosures, security checks, and safety-critical instructions.
- MEDIUM: Standard instructions that should be followed reliably, but where occasional lapses are tolerable. This is the default level, if unspecified.
- LOW: Instructions where occasional imperfection is acceptable. Examples include stylistic preferences or nice-to-have behavioral cues and nudges.



```
import parlant.sdk as pawait agent.create_guideline(    condition="Customer asks about cancellation fees",    action="Disclose the $50 cancellation fee before proceeding",    criticality=p.Criticality.HIGH)await agent.create_guideline(    condition="Customer wants to return an item",    action="Suggest store credit as an alternative to a refund",    criticality=p.Criticality.MEDIUM)await agent.create_guideline(    condition="The conversation has just started",    action="Inquire if they want to hear about on-sale items",    criticality=p.Criticality.LOW)
```



### Tool Consequentiality​


The same principle applies to tools. A read-only lookup like get_account_balance() carries different risk than a state-modifying operation like process_refund().


The consequential flag marks tools that require enhanced validation:



```
import parlant.sdk as p@p.tool  # Non-consequential (default, quick)async def get_order_status(    context: p.ToolContext,    order_id: str) -> p.ToolResult:    status = await orders_api.get_status(order_id)    return p.ToolResult(data=status)@p.tool(consequential=True)  # Consequential (more validation)async def process_refund(    context: p.ToolContext,    order_id: str,) -> p.ToolResult:    result = await payments_api.refund(order_id, amount)    return p.ToolResult(data=result)
```



## Handling Different Criticalities​



### How Criticality Affects Message Generation​


In Parlant 3.0, the message generator component assumes maximum criticality for all matched guidelines by strongly enforcing each one through specialized ARQs (structured reasoning patterns that guide the LLM to attend to specific instructions during generation).


This is why the correctness of guideline matching is so crucial in Parlant's architecture: Once a guideline reaches the message generator, Parlant will get it followed.


Incidentally, this creates a "be careful what you wish for" situation: your instructions will be adhered to, so it's important to design them so that they're matched only when truly applicable. This blessing can sometimes turn into a curse, as it places the burden on the guideline designer to craft precise conditions.


With the introduction of low-criticality guidelines in Parlant 3.1, this changes. Low-criticality guidelines will be included in the message generator's prompt, but won't be optimized through ARQs. They act as subtler, low-focus cues that the agent may incorporate when appropriate, rather than rigid requirements it conform to no matter what.



### Implications for Guideline Matching​


This distinction has an important implication for the potential efficiency and costs of guideline matching.


Because low-criticality guidelines don't trigger intensive ARQ enforcement, including one that isn't perfectly relevant to the current conversation state isn't particularly problematic.


For example, a false positive match on a low-criticality guideline might slightly influence the response, but won't derail it. This tolerance for "imprecision" in the matching requirements opens the door to more efficient matching schemes.


Case in point: at Emcie, our research team has recently been working on a low-pass filter for guidelines: a lightweight 4B model that quickly identifies which guidelines are sufficiently relevant before passing them to extended ARQ-based matching. Our current research shows roughly 70% accuracy with approximately 2% false positives, meaning about 1 in 50 guidelines might be incorrectly marked as relevant when it isn't.


Curiously, this enables a more efficient, tiered matching strategy:


1. LOW criticality: Use the low-pass filter directly. The 2% false-positive rate is acceptable given that these guidelines only provide subtle cues. This dramatically reduces compute costs for agents that make significant use of low-criticality guidelines.
2. MEDIUM criticality: Run the low-pass filter as a preliminary step, then apply extended ARQ-based reasoning only to guidelines that pass. The main concern here is false negatives—missing a guideline that should have matched—which we're actively optimizing for. But in any case, these guidelines aren't compliance-critical, so occasional misses are tolerable, by definition.
3. HIGH criticality: Always pass through extended ARQ-based matching. No shortcuts for compliance-critical instructions.


MessageGeneratorExtended ARQMatchingLow-Pass Filter(4B model)Guidelines#mermaid-svg-279494{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;fill:#000000;}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#mermaid-svg-279494 .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#mermaid-svg-279494 .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#mermaid-svg-279494 .error-icon{fill:#552222;}#mermaid-svg-279494 .error-text{fill:#552222;stroke:#552222;}#mermaid-svg-279494 .edge-thickness-normal{stroke-width:1px;}#mermaid-svg-279494 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-svg-279494 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-svg-279494 .edge-thickness-invisible{stroke-width:0;fill:none;}#mermaid-svg-279494 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-svg-279494 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-svg-279494 .marker{fill:#666;stroke:#666;}#mermaid-svg-279494 .marker.cross{stroke:#666;}#mermaid-svg-279494 svg{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;}#mermaid-svg-279494 p{margin:0;}#mermaid-svg-279494 .actor{stroke:hsl(0, 0%, 83%);fill:#eee;}#mermaid-svg-279494 text.actor>tspan{fill:#333;stroke:none;}#mermaid-svg-279494 .actor-line{stroke:hsl(0, 0%, 83%);}#mermaid-svg-279494 .messageLine0{stroke-width:1.5;stroke-dasharray:none;stroke:#333;}#mermaid-svg-279494 .messageLine1{stroke-width:1.5;stroke-dasharray:2,2;stroke:#333;}#mermaid-svg-279494 #arrowhead path{fill:#333;stroke:#333;}#mermaid-svg-279494 .sequenceNumber{fill:white;}#mermaid-svg-279494 #sequencenumber{fill:#333;}#mermaid-svg-279494 #crosshead path{fill:#333;stroke:#333;}#mermaid-svg-279494 .messageText{fill:#333;stroke:none;}#mermaid-svg-279494 .labelBox{stroke:hsl(0, 0%, 83%);fill:#eee;}#mermaid-svg-279494 .labelText,#mermaid-svg-279494 .labelText>tspan{fill:#333;stroke:none;}#mermaid-svg-279494 .loopText,#mermaid-svg-279494 .loopText>tspan{fill:#333;stroke:none;}#mermaid-svg-279494 .loopLine{stroke-width:2px;stroke-dasharray:2,2;stroke:hsl(0, 0%, 83%);fill:hsl(0, 0%, 83%);}#mermaid-svg-279494 .note{stroke:#999;fill:#666;}#mermaid-svg-279494 .noteText,#mermaid-svg-279494 .noteText>tspan{fill:#fff;stroke:none;}#mermaid-svg-279494 .activation0{fill:#f4f4f4;stroke:#666;}#mermaid-svg-279494 .activation1{fill:#f4f4f4;stroke:#666;}#mermaid-svg-279494 .activation2{fill:#f4f4f4;stroke:#666;}#mermaid-svg-279494 .actorPopupMenu{position:absolute;}#mermaid-svg-279494 .actorPopupMenuPanel{position:absolute;fill:#eee;box-shadow:0px 8px 16px 0px rgba(0,0,0,0.2);filter:drop-shadow(3px 5px 2px rgb(0 0 0 / 0.4));}#mermaid-svg-279494 .actor-man line{stroke:hsl(0, 0%, 83%);fill:#eee;}#mermaid-svg-279494 .actor-man circle,#mermaid-svg-279494 line{stroke:hsl(0, 0%, 83%);fill:#eee;stroke-width:2px;}#mermaid-svg-279494 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}Grouped by criticalityLOW criticalityPassed guidelines(as subtle cues)MEDIUM criticalityCandidatesMatched guidelinesHIGH criticalityMatched guidelines(full enforcement)

This approach has recently shown a lot of promise in our internal tests, and we plan to release it soon through our upcoming NLP inference service, which is specifically optimized for running Parlant agents in large-scale production.



## Assigning Criticality​


Having said all that, the key fact here is that we, as framework designers, often can't decide the criticality of instructions for you. This is a business decision that depends on your specific use case, risk tolerance, and operational context.


The question then becomes, how should you decide the criticality of your guidelines and tools?


Here are some recommendations.


- Default to MEDIUM, then adjust based on observed issues.
- Reserve HIGH for: compliance requirements, legal obligations, security checks, safety-critical instructions.
- Use LOW for: stylistic preferences and non-critical behavioral nudges. Use this whenever applicable to reduce operational costs..
- Mark tools as consequential when they modify state irreversibly or have significant financial impact.


And here's what to avoid:


- Marking everything HIGH negates the efficiency benefit, as it means you're back to uniform high-cost processing, which is often unnecessary.
- Marking everything LOW sacrifices reliability where it actually matters (although in some low-risk use cases this may be acceptable and can shave off multiple seconds of response latency).
- Using criticality as a band-aid for poorly specified guidelines. It's better to fix the guideline instead, if possible.



#### Decision Framework​


Ask two questions:


1. What is the consequence if the agent doesn't follow this perfectly?


Worst ConsequenceCriticalityLegal trouble or compliance riskHIGHDiminished business valueMEDIUMDiminished UX polishLOW
2. Does this tool modify state irreversibly?


AnswerSettingYes, or high financial impactconsequential=TrueNo, read-only or easily reversibleconsequential=False (default)

## Summary​


Criticality levels provide explicit control over the accuracy-cost tradeoff:


- HIGH, MEDIUM, and LOW map to different processing intensities for guidelines
- The consequential flag extends the same concept to tools
- Proper assignment requires understanding the business impact of each instruction


This allows you to maintain strong reliability guarantees where they matter (such as in compliance, security, and safety) while reducing overhead for stylistic preferences and non-critical behavioral tweaks.



---


For more details, see the Guidelines documentation and Tool documentation. Questions? Join us on Discord.

Share post:[](https://www.linkedin.com/shareArticle?mini=true&url=https://www.parlant.io/blog/criticality-in-customer-facing-agents/&text=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io)[](https://twitter.com/intent/tweet?url=https://www.parlant.io/blog/criticality-in-customer-facing-agents/&text=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io)[](https://www.facebook.com/sharer/sharer.php?u=https://www.parlant.io/blog/criticality-in-customer-facing-agents/)[](https://www.reddit.com/submit?url=https://www.parlant.io/blog/criticality-in-customer-facing-agents/&title=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io)[](https://bsky.app/intent/compose?text=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io%20%20https%3A%2F%2Fwww.parlant.io%2Fblog%2Fcriticality-in-customer-facing-agents%2F)Tags:parlantcriticalityconversational-aiguidelinestools
