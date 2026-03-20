---
title: "Inside Parlant's Guideline Matching Engine"
date: "November 1, 2025"
author: "Yam Marcovitz"
source: "https://www.parlant.io/blog/inside-parlant-guideline-matching-engine"
---

[](https://www.linkedin.com/in/yam-marcovic/)[Yam Marcovitz](https://www.linkedin.com/in/yam-marcovic/)Inside Parlant's Guideline Matching EngineNovember 1, 202543 min readConsider this. A customer messages your AI agent: "The shoes I ordered are the wrong size. I need to return them and get a new pair in my size. Is it possible? And how would the shipping fees work?"


To get our agent to handle this query correctly, there's some well-known but crucial components that must come into play.


- Number one, you need your knowledgebases. What's the general returns policy? What are the shipping rates for different regions?
- Number two, you need your API integrations. You need to load the customer's info, locate the order, verify its states, potentially initiate a refund, etc.
- Number three, you need your agent to handle all of this in line with your business rules: the expected sections of your knowledgebases need to be referenced at the right time; the correct APIs must be called in the right order; and the agent must process the ticket according to your approved business procedures.


Of course, this needs to happen correctly and consistently, virtually every time, across thousands of conversations, with dozens or hundreds of other guidelines coming into play.


However, providing all of this context to your LLM at the same time simply doesn't work. It doesn't really work for any of those things, but it particularly doesn't work when you need to ensure consistent adherence to business guidelines.


So filtering and selecting the right guidelines to apply at the right time is critical to deploying a trusted agent that can represent your business safely and correctly.


I've already written rigorously on why the most common orchestration patterns (e.g., supervisor and granular multi-agency) run into insurmountable challenges in real-world conversations, and why what's really needed is dynamic filtering and matching for every instruction in your system—at least those which can realistically end up being activated within a single multi-turn customer interaction.


Now, at first, this filtering process can sound deceptively simple: Throughout the conversation, just retrieve and match the relevant guidelines before each response and include them in the prompt, just like you do with classic RAG. Right?


That's what we thought when we started building Parlant, but we were extraordinarily wrong. What we hoped would be a 3-month project turned into a year-long journey of research, experimentation, and iteration of an experienced 10-person team of developers and NLP researchers.


Sounds crazy?


In this post, I'm diving into what it actually took to make Parlant's guideline matching work reliably at scale: with real-world customer scenarios and business constraints.


[Grill us on Discord](https://discord.gg/duxWqxKk6J)
Contents:


- Understanding "Reliability"The Curse of InstructionsThe Trust AspectThe Feedback Cycle AspectThe Compliance Aspect
- It's Harder Than You're (Probably) ThinkingInitial Failed ApproachesThe Core IssueThe Switch to LLMsThe Latency Challenge
- The Cost ChallengeParallel ExecutionRelational ResolutionThe Preparation Iteration LoopPre-Evaluation and Optimization
- Attentive Reasoning Queries (ARQs)What Are ARQs?ARQs Per Guideline Category
- But Is All of This Really Necessary?Test Suite ExamplesContinuous Performance Improvement
- The Big Picture
- The Road AheadBe a Part of the Vision



## Understanding "Reliability"​


Before diving into the technical complexity, let's first establish what makes this a technical challenge in the first place.


When you start building a conversational AI agent with LLMs, you might have 5-10 behavioral guidelines. That's manageable with simple approaches.


Six months into production, you have over 100 business guidelines, easily. Different customer scenarios, compliance requirements, regional variations, product-specific rules. Business experts keep finding edge cases that need handling. This is natural.


A year in, you're at hundreds of guidelines. Some apply globally. Some only to specific customer segments. Some only during particular conversation states. Many depend on temporal, shifting context within a single conversation.



### The Curse of Instructions​


As you add more guidelines, you quickly run into a hard fundamental limitation of LLMs, which is The Curse of Instructions.


![The Curse of Instructions](https://www.parlant.io/img/curse-of-instructions.png)


The issue is that, as you add more instructions to an LLM's context, its ability to follow them drops dramatically. Not even linearly (which would be bad enough), but dramatically.


Let the implications of that sink in for a moment.


Now, rather than being a particular model's weakness, it unfortunately seems like a fundamental architectural challenge with LLMs, and it applies across the board with every LLM you use. It's why planning and orchestration are the most important differentiating components of any agentic system you encounter.


It's also why Parlant's guideline matching system came into existence. Its core purpose is to "lift the curse" by ensuring your LLM only sees the few most relevant guidelines (and other domain alignment elements) at each point, keeping the model in the "safe zone" where instruction-following is highly consistent:






### The Trust Aspect​


When you finally deploy your agent to production, you run into real-world user issues, which are, for lack of a better term... messy.


Now, by that time, keep in mind you'll have probably spent months building your agent, but if customers ultimately don't trust it to handle their specific situation correctly, they'll escalate to a human immediately, rendering your investment (the time, effort, and budget you've put into it) significantly less rewarding than you'd hoped.


But how can you ensure that customers trust your agent and engage with it?


The interesting (and more realistic) answer is that, unfortunately, you don't—at least not if you're a developer. It almost always comes down to business stakeholders providing continual feedback (and experimentation), monitoring conversations, and adjusting the agent's behavior over time.


Business stakeholders have a more direct line of sight into customer expectations and pain points, and, not least important is that they also typically have a greater incentive to experiment with the agent's communication effectiveness and optimize it, compared to the engineers on the project.



### The Feedback Cycle Aspect​


This is why business experts will constantly provide feedback on agent behavior. While this kind of feedback may not be the most glamorous work to implement as an engineer, it can nonetheless play a pivotal role in the agent's production success metrics.


Let's look at a few examples of real-world feedback from business stakeholders:


- "We don't accept Amex cards. It's just misleading the customers and eroding trust, leading to escalation. So before trying and failing, when they provide Amex it should ask them if they have a different card or, alternatively, offer PayPal as a last resort (but make sure you don't mention PayPal until you ascertain they don't have a different card they can use)."
- "This customer wants to buy in bulk. That's great but we should get them on a sales call, not handle it here, as the pricing on bulk orders needs to be negotiated."
- "This customer just had a bad experience with us; why would you take this opportunity—of all times—to try and upsell them!?"


When such feedback arrives, it often requires reliable correction within hours or days.


Your agent's guideline matching and enforcement system is what makes this feedback cycle possible.


Without a reliable and flexible guideline matching system, every behavioral change can turn into its own task sprint, instead of a quick configuration update. It's hard to isolate the required changes and it's hard to avoid breaking other parts of the agent's behavior.


This ends up being a slow, error-prone, and expensive maintenance process for the whole team.



### The Compliance Aspect​


Let's talk about compliance for a moment. For regulated industries, adherence to business guidelines is, in many cases, non-negotiable.


Every unauthorized statement made by your agent increases the chances for liability and some form of action taken against your organization. Even simply missing a disclosure at the right time in a conversation can create regulatory risk. At scale, one guideline failure in 1,000 conversations can unfortunately mean trouble.


This is why architectural guarantees are so important; so that guidelines will be evaluated and followed as reliably and accurately as possible. Even if you play the game of odds here, your architecture must ensure they're very good odds, while also allowing you to improve over time, without breaking existing stabilized behavior. In other words, the mechanism must maintain robustness even as your agent's complexity grows with further real-world feedback.



#mermaid-svg-1177496{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;fill:#000000;}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#mermaid-svg-1177496 .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#mermaid-svg-1177496 .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#mermaid-svg-1177496 .error-icon{fill:#552222;}#mermaid-svg-1177496 .error-text{fill:#552222;stroke:#552222;}#mermaid-svg-1177496 .edge-thickness-normal{stroke-width:1px;}#mermaid-svg-1177496 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-svg-1177496 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-svg-1177496 .edge-thickness-invisible{stroke-width:0;fill:none;}#mermaid-svg-1177496 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-svg-1177496 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-svg-1177496 .marker{fill:#666;stroke:#666;}#mermaid-svg-1177496 .marker.cross{stroke:#666;}#mermaid-svg-1177496 svg{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;}#mermaid-svg-1177496 p{margin:0;}#mermaid-svg-1177496 .label{font-family:"trebuchet ms",verdana,arial,sans-serif;color:#000000;}#mermaid-svg-1177496 .cluster-label text{fill:#333;}#mermaid-svg-1177496 .cluster-label span{color:#333;}#mermaid-svg-1177496 .cluster-label span p{background-color:transparent;}#mermaid-svg-1177496 .label text,#mermaid-svg-1177496 span{fill:#000000;color:#000000;}#mermaid-svg-1177496 .node rect,#mermaid-svg-1177496 .node circle,#mermaid-svg-1177496 .node ellipse,#mermaid-svg-1177496 .node polygon,#mermaid-svg-1177496 .node path{fill:#eee;stroke:#999;stroke-width:1px;}#mermaid-svg-1177496 .rough-node .label text,#mermaid-svg-1177496 .node .label text,#mermaid-svg-1177496 .image-shape .label,#mermaid-svg-1177496 .icon-shape .label{text-anchor:middle;}#mermaid-svg-1177496 .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#mermaid-svg-1177496 .rough-node .label,#mermaid-svg-1177496 .node .label,#mermaid-svg-1177496 .image-shape .label,#mermaid-svg-1177496 .icon-shape .label{text-align:center;}#mermaid-svg-1177496 .node.clickable{cursor:pointer;}#mermaid-svg-1177496 .root .anchor path{fill:#666!important;stroke-width:0;stroke:#666;}#mermaid-svg-1177496 .arrowheadPath{fill:#333333;}#mermaid-svg-1177496 .edgePath .path{stroke:#666;stroke-width:2.0px;}#mermaid-svg-1177496 .flowchart-link{stroke:#666;fill:none;}#mermaid-svg-1177496 .edgeLabel{background-color:white;text-align:center;}#mermaid-svg-1177496 .edgeLabel p{background-color:white;}#mermaid-svg-1177496 .edgeLabel rect{opacity:0.5;background-color:white;fill:white;}#mermaid-svg-1177496 .labelBkg{background-color:rgba(255, 255, 255, 0.5);}#mermaid-svg-1177496 .cluster rect{fill:hsl(0, 0%, 98.9215686275%);stroke:#707070;stroke-width:1px;}#mermaid-svg-1177496 .cluster text{fill:#333;}#mermaid-svg-1177496 .cluster span{color:#333;}#mermaid-svg-1177496 div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:12px;background:hsl(-160, 0%, 93.3333333333%);border:1px solid #707070;border-radius:2px;pointer-events:none;z-index:100;}#mermaid-svg-1177496 .flowchartTitleText{text-anchor:middle;font-size:18px;fill:#000000;}#mermaid-svg-1177496 rect.text{fill:none;stroke-width:0;}#mermaid-svg-1177496 .icon-shape,#mermaid-svg-1177496 .image-shape{background-color:white;text-align:center;}#mermaid-svg-1177496 .icon-shape p,#mermaid-svg-1177496 .image-shape p{background-color:white;padding:2px;}#mermaid-svg-1177496 .icon-shape rect,#mermaid-svg-1177496 .image-shape rect{opacity:0.5;background-color:white;fill:white;}#mermaid-svg-1177496 .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#mermaid-svg-1177496 .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#mermaid-svg-1177496 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}Adds/UpdatesControlConversationsFeedbackBehavior IssuesBusiness ExpertGuidelinesAI AgentCustomers
[Share your production experience with us](https://discord.gg/duxWqxKk6J)

## It's Harder Than You're (Probably) Thinking​


Let us begin our dive into the technical parts.


When we started building Parlant's guideline matching system, our first instinct was to employ approaches such comparing the semantic similarity of content embeddings, using cross-encoders, or possibly training custom task-head architectures on top.


It seemed elegant: encode guidelines and conversation context as vectors, compute their relevance score (depending on the method), and load the matches which pass the minimal threshold.



### Initial Failed Approaches​


We tried all three different approaches before facing the fact that they failed to solve the problem reliably.



#### Approach 1: Semantic Similarity​


Honestly, we already knew semantic similarity wasn't going to work before we tried it, but we studied it anyway.


The idea: Embed guidelines and conversation, compute cosine similarity between the conversation and each guideline, and match the most similar guidelines—or at least ones passing a threshold.



#mermaid-svg-1854779{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;fill:#000000;}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#mermaid-svg-1854779 .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#mermaid-svg-1854779 .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#mermaid-svg-1854779 .error-icon{fill:#552222;}#mermaid-svg-1854779 .error-text{fill:#552222;stroke:#552222;}#mermaid-svg-1854779 .edge-thickness-normal{stroke-width:1px;}#mermaid-svg-1854779 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-svg-1854779 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-svg-1854779 .edge-thickness-invisible{stroke-width:0;fill:none;}#mermaid-svg-1854779 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-svg-1854779 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-svg-1854779 .marker{fill:#666;stroke:#666;}#mermaid-svg-1854779 .marker.cross{stroke:#666;}#mermaid-svg-1854779 svg{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;}#mermaid-svg-1854779 p{margin:0;}#mermaid-svg-1854779 .label{font-family:"trebuchet ms",verdana,arial,sans-serif;color:#000000;}#mermaid-svg-1854779 .cluster-label text{fill:#333;}#mermaid-svg-1854779 .cluster-label span{color:#333;}#mermaid-svg-1854779 .cluster-label span p{background-color:transparent;}#mermaid-svg-1854779 .label text,#mermaid-svg-1854779 span{fill:#000000;color:#000000;}#mermaid-svg-1854779 .node rect,#mermaid-svg-1854779 .node circle,#mermaid-svg-1854779 .node ellipse,#mermaid-svg-1854779 .node polygon,#mermaid-svg-1854779 .node path{fill:#eee;stroke:#999;stroke-width:1px;}#mermaid-svg-1854779 .rough-node .label text,#mermaid-svg-1854779 .node .label text,#mermaid-svg-1854779 .image-shape .label,#mermaid-svg-1854779 .icon-shape .label{text-anchor:middle;}#mermaid-svg-1854779 .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#mermaid-svg-1854779 .rough-node .label,#mermaid-svg-1854779 .node .label,#mermaid-svg-1854779 .image-shape .label,#mermaid-svg-1854779 .icon-shape .label{text-align:center;}#mermaid-svg-1854779 .node.clickable{cursor:pointer;}#mermaid-svg-1854779 .root .anchor path{fill:#666!important;stroke-width:0;stroke:#666;}#mermaid-svg-1854779 .arrowheadPath{fill:#333333;}#mermaid-svg-1854779 .edgePath .path{stroke:#666;stroke-width:2.0px;}#mermaid-svg-1854779 .flowchart-link{stroke:#666;fill:none;}#mermaid-svg-1854779 .edgeLabel{background-color:white;text-align:center;}#mermaid-svg-1854779 .edgeLabel p{background-color:white;}#mermaid-svg-1854779 .edgeLabel rect{opacity:0.5;background-color:white;fill:white;}#mermaid-svg-1854779 .labelBkg{background-color:rgba(255, 255, 255, 0.5);}#mermaid-svg-1854779 .cluster rect{fill:hsl(0, 0%, 98.9215686275%);stroke:#707070;stroke-width:1px;}#mermaid-svg-1854779 .cluster text{fill:#333;}#mermaid-svg-1854779 .cluster span{color:#333;}#mermaid-svg-1854779 div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:12px;background:hsl(-160, 0%, 93.3333333333%);border:1px solid #707070;border-radius:2px;pointer-events:none;z-index:100;}#mermaid-svg-1854779 .flowchartTitleText{text-anchor:middle;font-size:18px;fill:#000000;}#mermaid-svg-1854779 rect.text{fill:none;stroke-width:0;}#mermaid-svg-1854779 .icon-shape,#mermaid-svg-1854779 .image-shape{background-color:white;text-align:center;}#mermaid-svg-1854779 .icon-shape p,#mermaid-svg-1854779 .image-shape p{background-color:white;padding:2px;}#mermaid-svg-1854779 .icon-shape rect,#mermaid-svg-1854779 .image-shape rect{opacity:0.5;background-color:white;fill:white;}#mermaid-svg-1854779 .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#mermaid-svg-1854779 .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#mermaid-svg-1854779 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}Guideline 1EmbeddingVector 1Guideline NEmbeddingVector NConversationHistoryConversationEmbeddingCosine SimilarityComputationScore: 0.87Score: 0.65Score: 0.43Match Guideline 1

Why it failed: Guidelines often refer to chronological or other semantic nuances, but we couldn't find a single pretrained embedding model that captures them well (and I'll circle back to why we didn't train our own). Think of conditions such as temporal ones ("Card already declined"), logical ones ("AND payment is credit card"), or state transitions ("After confirming the transaction").



#### Approach 2: Cross-Encoders​


Unlike semantic similarity where you embed texts separately and compare vectors, cross-encoders jointly process the guideline and conversation together through a transformer model (like BERT or RoBERTa).


The idea: Feed each guideline-conversation pair into the encoder, let attention mechanisms learn interactions between them, then use a classification head to predict relevance.



#mermaid-svg-3824170{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;fill:#000000;}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#mermaid-svg-3824170 .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#mermaid-svg-3824170 .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#mermaid-svg-3824170 .error-icon{fill:#552222;}#mermaid-svg-3824170 .error-text{fill:#552222;stroke:#552222;}#mermaid-svg-3824170 .edge-thickness-normal{stroke-width:1px;}#mermaid-svg-3824170 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-svg-3824170 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-svg-3824170 .edge-thickness-invisible{stroke-width:0;fill:none;}#mermaid-svg-3824170 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-svg-3824170 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-svg-3824170 .marker{fill:#666;stroke:#666;}#mermaid-svg-3824170 .marker.cross{stroke:#666;}#mermaid-svg-3824170 svg{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;}#mermaid-svg-3824170 p{margin:0;}#mermaid-svg-3824170 .label{font-family:"trebuchet ms",verdana,arial,sans-serif;color:#000000;}#mermaid-svg-3824170 .cluster-label text{fill:#333;}#mermaid-svg-3824170 .cluster-label span{color:#333;}#mermaid-svg-3824170 .cluster-label span p{background-color:transparent;}#mermaid-svg-3824170 .label text,#mermaid-svg-3824170 span{fill:#000000;color:#000000;}#mermaid-svg-3824170 .node rect,#mermaid-svg-3824170 .node circle,#mermaid-svg-3824170 .node ellipse,#mermaid-svg-3824170 .node polygon,#mermaid-svg-3824170 .node path{fill:#eee;stroke:#999;stroke-width:1px;}#mermaid-svg-3824170 .rough-node .label text,#mermaid-svg-3824170 .node .label text,#mermaid-svg-3824170 .image-shape .label,#mermaid-svg-3824170 .icon-shape .label{text-anchor:middle;}#mermaid-svg-3824170 .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#mermaid-svg-3824170 .rough-node .label,#mermaid-svg-3824170 .node .label,#mermaid-svg-3824170 .image-shape .label,#mermaid-svg-3824170 .icon-shape .label{text-align:center;}#mermaid-svg-3824170 .node.clickable{cursor:pointer;}#mermaid-svg-3824170 .root .anchor path{fill:#666!important;stroke-width:0;stroke:#666;}#mermaid-svg-3824170 .arrowheadPath{fill:#333333;}#mermaid-svg-3824170 .edgePath .path{stroke:#666;stroke-width:2.0px;}#mermaid-svg-3824170 .flowchart-link{stroke:#666;fill:none;}#mermaid-svg-3824170 .edgeLabel{background-color:white;text-align:center;}#mermaid-svg-3824170 .edgeLabel p{background-color:white;}#mermaid-svg-3824170 .edgeLabel rect{opacity:0.5;background-color:white;fill:white;}#mermaid-svg-3824170 .labelBkg{background-color:rgba(255, 255, 255, 0.5);}#mermaid-svg-3824170 .cluster rect{fill:hsl(0, 0%, 98.9215686275%);stroke:#707070;stroke-width:1px;}#mermaid-svg-3824170 .cluster text{fill:#333;}#mermaid-svg-3824170 .cluster span{color:#333;}#mermaid-svg-3824170 div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:12px;background:hsl(-160, 0%, 93.3333333333%);border:1px solid #707070;border-radius:2px;pointer-events:none;z-index:100;}#mermaid-svg-3824170 .flowchartTitleText{text-anchor:middle;font-size:18px;fill:#000000;}#mermaid-svg-3824170 rect.text{fill:none;stroke-width:0;}#mermaid-svg-3824170 .icon-shape,#mermaid-svg-3824170 .image-shape{background-color:white;text-align:center;}#mermaid-svg-3824170 .icon-shape p,#mermaid-svg-3824170 .image-shape p{background-color:white;padding:2px;}#mermaid-svg-3824170 .icon-shape rect,#mermaid-svg-3824170 .image-shape rect{opacity:0.5;background-color:white;fill:white;}#mermaid-svg-3824170 .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#mermaid-svg-3824170 .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#mermaid-svg-3824170 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}GuidelineGuideline +ConversationPairConversationCross-EncoderBERT/RoBERTaCLS TokenRepresentationClassifierHeadRelevanceScore: 0.87

The cross-encoder processes both texts together, so theoretically it should capture relationships between them better than independent embeddings. You train it on labeled examples of (guideline, conversation, relevant/not-relevant) tuples.


Why it failed: Much like the embedding approach, all pretrained cross-encoders that we've tried (anything that showed potential on SBERT and HF) struggled heavily with the specific nuances of guideline matching.



#### Approach 3: Task-Specific Neural Network Head​


The idea here was to train a simple neural network layer on top of embeddings taken from pretrained models. We assumed that extracting embeddings from the last hidden layers of pretrained models would provide useful features for the task. This task head would then be trained from scratch specifically for guideline matching.



#mermaid-svg-5407235{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;fill:#000000;}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#mermaid-svg-5407235 .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#mermaid-svg-5407235 .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#mermaid-svg-5407235 .error-icon{fill:#552222;}#mermaid-svg-5407235 .error-text{fill:#552222;stroke:#552222;}#mermaid-svg-5407235 .edge-thickness-normal{stroke-width:1px;}#mermaid-svg-5407235 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-svg-5407235 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-svg-5407235 .edge-thickness-invisible{stroke-width:0;fill:none;}#mermaid-svg-5407235 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-svg-5407235 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-svg-5407235 .marker{fill:#666;stroke:#666;}#mermaid-svg-5407235 .marker.cross{stroke:#666;}#mermaid-svg-5407235 svg{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;}#mermaid-svg-5407235 p{margin:0;}#mermaid-svg-5407235 .label{font-family:"trebuchet ms",verdana,arial,sans-serif;color:#000000;}#mermaid-svg-5407235 .cluster-label text{fill:#333;}#mermaid-svg-5407235 .cluster-label span{color:#333;}#mermaid-svg-5407235 .cluster-label span p{background-color:transparent;}#mermaid-svg-5407235 .label text,#mermaid-svg-5407235 span{fill:#000000;color:#000000;}#mermaid-svg-5407235 .node rect,#mermaid-svg-5407235 .node circle,#mermaid-svg-5407235 .node ellipse,#mermaid-svg-5407235 .node polygon,#mermaid-svg-5407235 .node path{fill:#eee;stroke:#999;stroke-width:1px;}#mermaid-svg-5407235 .rough-node .label text,#mermaid-svg-5407235 .node .label text,#mermaid-svg-5407235 .image-shape .label,#mermaid-svg-5407235 .icon-shape .label{text-anchor:middle;}#mermaid-svg-5407235 .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#mermaid-svg-5407235 .rough-node .label,#mermaid-svg-5407235 .node .label,#mermaid-svg-5407235 .image-shape .label,#mermaid-svg-5407235 .icon-shape .label{text-align:center;}#mermaid-svg-5407235 .node.clickable{cursor:pointer;}#mermaid-svg-5407235 .root .anchor path{fill:#666!important;stroke-width:0;stroke:#666;}#mermaid-svg-5407235 .arrowheadPath{fill:#333333;}#mermaid-svg-5407235 .edgePath .path{stroke:#666;stroke-width:2.0px;}#mermaid-svg-5407235 .flowchart-link{stroke:#666;fill:none;}#mermaid-svg-5407235 .edgeLabel{background-color:white;text-align:center;}#mermaid-svg-5407235 .edgeLabel p{background-color:white;}#mermaid-svg-5407235 .edgeLabel rect{opacity:0.5;background-color:white;fill:white;}#mermaid-svg-5407235 .labelBkg{background-color:rgba(255, 255, 255, 0.5);}#mermaid-svg-5407235 .cluster rect{fill:hsl(0, 0%, 98.9215686275%);stroke:#707070;stroke-width:1px;}#mermaid-svg-5407235 .cluster text{fill:#333;}#mermaid-svg-5407235 .cluster span{color:#333;}#mermaid-svg-5407235 div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:12px;background:hsl(-160, 0%, 93.3333333333%);border:1px solid #707070;border-radius:2px;pointer-events:none;z-index:100;}#mermaid-svg-5407235 .flowchartTitleText{text-anchor:middle;font-size:18px;fill:#000000;}#mermaid-svg-5407235 rect.text{fill:none;stroke-width:0;}#mermaid-svg-5407235 .icon-shape,#mermaid-svg-5407235 .image-shape{background-color:white;text-align:center;}#mermaid-svg-5407235 .icon-shape p,#mermaid-svg-5407235 .image-shape p{background-color:white;padding:2px;}#mermaid-svg-5407235 .icon-shape rect,#mermaid-svg-5407235 .image-shape rect{opacity:0.5;background-color:white;fill:white;}#mermaid-svg-5407235 .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#mermaid-svg-5407235 .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#mermaid-svg-5407235 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}GuidelineGuidelineEmbeddingConversationConversationEmbeddingConcatenateNeural Layer 1512 unitsNeural Layer 2256 unitsNeural Layer 3128 unitsOutput LayerBinary: Match/No Match

But regardless of the embedding source, they just didn't seem to contain enough real information for the task head to learn from.


We trained it on a huge number of examples taken from the Ubuntu Dialog Corpus, but the task head just didn't learn.


Why it failed: No matter how we tuned the architecture or training process, the embeddings appeared to be too lossy. Critical information about chronology, logical operators, and state transitions seems to get compressed away in the final vector representation, and the learning process never converged.



### The Core Issue​


We initially assumed that embeddings from pretrained models would contain enough information about relationships between vectors (e.g., between conversations and guidelines).


The hope was that these vector representations would encode the nuanced relationships we needed for matching. But in reality they didn't seem to contain that information in any learnable form. None of the approaches we tried managed to learn the desired behavior.


Now as to why we didn't design and train our own specialized embedding or cross-encoder models for guideline matching from scratch: it simply wasn't feasible. Such an undertaking would require truly massive datasets and carry significant risk (what if by the end of it, these models still couldn't learn?)


We therefore chose to stand on the shoulders of giants. LLMs, unlike specialized embedding models, were trained not just for language understanding but also for reasoning, instruction following, and text completion. These capabilities made them natural candidates for guideline matching, even if that meant working through the latency and cost challenges that came with them.


Subject of Active ResearchWe haven't given up on these initial approaches entirely; they're a subject of active research within our team. If you have ideas or experience in this area, we'd love to hear from you, as we'll continually push research boundaries to make guideline matching more efficient.

[Researching NLP? Let's Connect!](https://discord.gg/duxWqxKk6J)
In short, all of the initial approaches we tried failed miserably to capture critical aspects of guideline matching. Let's see what these are, more concretely:


Conversational Chronology


Consider this guideline:



```
await agent.create_guideline(    condition="The customer has already declined an upgrade offer",    action="Do not mention upgrades again in this session")
```


Models trained on general semantic similarity can tell you that the conversation involves "upgrades" and "declining." But they couldn't reliably us you whether the customer already declined during this conversation, and consequently whether the instruction should be matched once again (and consequently enforced).


Nuanced Context



```
await agent.create_guideline(    condition="The customer is having difficulty in making the payment",    action="Transfer the call to a human agent immediately")
```


If a customer says, "I don't have my card with me right now," this guideline would be unlikely to pass the semantic similarity threshold.


In fact, conditions such as, "The customer is being difficult", or, "The customer is willing to pay immediately" are more likely to match—leading to false-positive matches that steer the conversation even further away from its intended path.


Temporal State Reasoning



```
await agent.create_guideline(    condition="After you've verified the customer's identity",    action="You may discuss account-specific billing details")
```


The word "after" creates a causal dependency. Again, semantic similarity won't capture this temporal relationship, leading to many false-positive as well as false-negative activations.


[Think we missed an interesting approach?](https://discord.gg/duxWqxKk6J)

### The Switch to LLMs​


At this point, we made a pragmatic choice: rather than investing in building and training dedicated guideline matching datasets and models (which would be infeasible at a realistic budget and timeline) we decided to leverage pretrained LLMs for the time being. Their training already equipped them for reasoning and instruction-following, making them well-suited for this task.


At first, we thought this would be straightforward: just write a prompt to say, "reason about the context for a bit and tell me whether this guideline currently applies."


LLMs are smart...right?


It turns out that once you start measuring their consistency across many real-world scenarios, their outputs can be very, very frustrating.


Sure, some guidelines are trivial to match:



```
await agent.create_guideline(    condition="The customer asks about store hours",    action="Tell them we're open Monday-Friday 9-8...")
```


This needs minimal reasoning. Does the conversation mention store hours? Yes or no.


But the problem is that people need, and use, much more nuanced guidelines.



```
await agent.create_guideline(    condition="User exhibits frustration with what you JUST offered",    action="Apologize and offer to transfer them to a human rep")
```


What exactly is meant by "exhibits frustration"? The customer doesn't necessarily use the word "frustrated." It might be implied through sarcasm, terse responses, or references to prior problems.



```
await agent.create_guideline(    condition="The customer needs to perform an action with their card "              "but it isn't exactly clear what that action is",    action="Ask them to clarify what action they wish to take")
```


When we were on this level of the implementation, we saw this match in intended cases:



> Customer: "card help plz"
Agent: "Could you please clarify what you need help you need with it?"
(Agent Reasoning): "The customer mentioned needing help with their card, but it's not clear what specific action they want to take. Therefore, this guideline applies."


As well as unintended ones:



> Customer: "I need to lock my card"
Agent: "Could you please clarify what you need help you need with it?"
(Agent Reasoning): "The customer needs to lock their card, which is a form of card-related help, but it isn't clear what they want to do once their card is locked. Therefore, this guideline applies."


At this point, we were like... 🤷‍♂


So we started evolving our matching prompt. We got it to the point where it was indeed incredibly accurate and consistent! The problem was, it used so much reasoning that it took like 20 seconds to run—before each response!


That's when we realized that this problem is deeper and more complex than we thought... and that all of these subtleties mean that if you use the same matching strategy for both, you either:


1. Waste compute on the simple cases with unnecessarily deep reasoning
2. Fail on the complex or nuanced cases with insufficient reasoning


To fix this latency issue, over time we studied many use cases and conversational scenarios, and empirically discovered and optimized for six distinct categories of guidelines, each requiring specialized matching strategies:


1. Observational Guidelines (condition only, no action)



```
condition="The customer mentioned a discount code"
```


These record facts about the conversation for other guidelines to reference (usually this is used in deliberate dependency relationships, so as to enable certain guidelines only if certain observations currently apply, which helps to avoid context collision and false positives). These need quick pattern matching.


Incidentally, even these aren't quite trivial. People will often write conditions such as, "The customer said they want to buy a ticket". When exactly should we consider this matched? Only in the immediate next response, throughout the conversation, or only during some particular segment of the conversation?


2. Simple Actionable Guidelines



```
condition="The customer asks about warranty coverage"action="Explain our standard 1-year warranty on all products"
```


These are the most standard condition-action guidelines. They require moderate reasoning, such as observational ones, to evaluate the condition accurately.


The reason they're in a different category is because people will often write conditions that refer to semantics in the action that they specified, such as:



> Action: "Provide the confirmed transaction ID"
Condition: "As soon as it's successfully completed"


If we tried to match this guideline only using its condition, we wouldn't know what "it" refers to. So both of them need to be considered in the specialized prompt for this category.


3. Previously Applied Actionable Guidelines



```
condition="The customer wants to return an item"action="Explain the 30-day return policy and ask for their order number"
```


These need special handling: If we already followed this guideline earlier in the conversation, should we apply it again (e.g., due to a sufficiently significant contextual shift)? Or would that cause artificially repetitive behavior?


The interesting thing to note here is that understanding whether an action was applied can be surprisingly tricky, even with LLMs.


Let's take two real-world examples we had to solve:


1. Often, if the action is something like, "Ask for order number", the agent would ask, and the customer would occasionally ignore the question in their next response. Then we found that the LLM would say, "Oh, the action was already applied, so I don't need to do it again", and the conversation would get derailed. When we looked at the reasoning logs, the LLM said, "Well, I already asked for the order number, so I don't need to ask again." This is one taste of the nuance and complexity involved.
2. Even after we fixed that first problem, it turns out that in practice people often provide compound actions ("Determine their order number and then explain our refund policy"). Then if only part of the action was applied, the LLM would often say (erroneously), "Oh, I already did that action, so I don't need to repeat it". This required us to implement partial action tracking and reasoning.


Both of these issues required even more structured reasoning in order to get them to work well consistently. But this extra reasoning came at the cost of latency. I'll circle back to this in a bit.


4. Customer-Dependent Actionable Guidelines



```
condition="The customer wants to send money"action="Ask for recipient name"
```


This is the most special case. Like I said above, with normal actionable guidelines, we need to keep track of whether the actions were already performed.


But what happens in the guideline above where you cannot determine if it was performed just based on the agent's message? The action above, strictly speaking, could only be considered completed if the customer actually provided the recipient name in their next message.


This means that we can't reason about it asynchronously after the agent's message is sent, because we need to wait for the customer's next message to see if the action was actually completed.


So in order to save more latency, we specialized a prompt for this special case.


5. Journey Node Selection


When a multi-step journey is active, which step should execute next? This requires reasoning about current journey state, transition conditions between steps, and the customer's latest input.


I won't even discuss this here as it's a whole other level of complexity. Read the code if you're interested: journey_node_selection_batch.py.


6. Disambiguation Guidelines



```
condition="The customer mentions they want to 'upgrade' "          "without being clear on what they wish to upgrade"# Targets: [#   upgrade_subscription_tier,#   upgrade_product_model,#   upgrade_shipping,# ]
```


This special category—disambiguating between specific, supported actions—required us to build a custom prompt that presents the possible targets (the ones specifically provided by the designer) and asks the LLM—only when needed—do disambiguate among them.


In case of a likely ambiguity, this strategy would yield a "virtual" temporary guideline, which would instruct the agent to ask for a clarification among the subset of options for which ambiguity was detected.


Guideline Matching Architecture at a Glance:



#mermaid-svg-5462422{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;fill:#000000;}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#mermaid-svg-5462422 .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#mermaid-svg-5462422 .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#mermaid-svg-5462422 .error-icon{fill:#552222;}#mermaid-svg-5462422 .error-text{fill:#552222;stroke:#552222;}#mermaid-svg-5462422 .edge-thickness-normal{stroke-width:1px;}#mermaid-svg-5462422 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-svg-5462422 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-svg-5462422 .edge-thickness-invisible{stroke-width:0;fill:none;}#mermaid-svg-5462422 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-svg-5462422 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-svg-5462422 .marker{fill:#666;stroke:#666;}#mermaid-svg-5462422 .marker.cross{stroke:#666;}#mermaid-svg-5462422 svg{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;}#mermaid-svg-5462422 p{margin:0;}#mermaid-svg-5462422 .label{font-family:"trebuchet ms",verdana,arial,sans-serif;color:#000000;}#mermaid-svg-5462422 .cluster-label text{fill:#333;}#mermaid-svg-5462422 .cluster-label span{color:#333;}#mermaid-svg-5462422 .cluster-label span p{background-color:transparent;}#mermaid-svg-5462422 .label text,#mermaid-svg-5462422 span{fill:#000000;color:#000000;}#mermaid-svg-5462422 .node rect,#mermaid-svg-5462422 .node circle,#mermaid-svg-5462422 .node ellipse,#mermaid-svg-5462422 .node polygon,#mermaid-svg-5462422 .node path{fill:#eee;stroke:#999;stroke-width:1px;}#mermaid-svg-5462422 .rough-node .label text,#mermaid-svg-5462422 .node .label text,#mermaid-svg-5462422 .image-shape .label,#mermaid-svg-5462422 .icon-shape .label{text-anchor:middle;}#mermaid-svg-5462422 .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#mermaid-svg-5462422 .rough-node .label,#mermaid-svg-5462422 .node .label,#mermaid-svg-5462422 .image-shape .label,#mermaid-svg-5462422 .icon-shape .label{text-align:center;}#mermaid-svg-5462422 .node.clickable{cursor:pointer;}#mermaid-svg-5462422 .root .anchor path{fill:#666!important;stroke-width:0;stroke:#666;}#mermaid-svg-5462422 .arrowheadPath{fill:#333333;}#mermaid-svg-5462422 .edgePath .path{stroke:#666;stroke-width:2.0px;}#mermaid-svg-5462422 .flowchart-link{stroke:#666;fill:none;}#mermaid-svg-5462422 .edgeLabel{background-color:white;text-align:center;}#mermaid-svg-5462422 .edgeLabel p{background-color:white;}#mermaid-svg-5462422 .edgeLabel rect{opacity:0.5;background-color:white;fill:white;}#mermaid-svg-5462422 .labelBkg{background-color:rgba(255, 255, 255, 0.5);}#mermaid-svg-5462422 .cluster rect{fill:hsl(0, 0%, 98.9215686275%);stroke:#707070;stroke-width:1px;}#mermaid-svg-5462422 .cluster text{fill:#333;}#mermaid-svg-5462422 .cluster span{color:#333;}#mermaid-svg-5462422 div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:12px;background:hsl(-160, 0%, 93.3333333333%);border:1px solid #707070;border-radius:2px;pointer-events:none;z-index:100;}#mermaid-svg-5462422 .flowchartTitleText{text-anchor:middle;font-size:18px;fill:#000000;}#mermaid-svg-5462422 rect.text{fill:none;stroke-width:0;}#mermaid-svg-5462422 .icon-shape,#mermaid-svg-5462422 .image-shape{background-color:white;text-align:center;}#mermaid-svg-5462422 .icon-shape p,#mermaid-svg-5462422 .image-shape p{background-color:white;padding:2px;}#mermaid-svg-5462422 .icon-shape rect,#mermaid-svg-5462422 .image-shape rect{opacity:0.5;background-color:white;fill:white;}#mermaid-svg-5462422 .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#mermaid-svg-5462422 .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#mermaid-svg-5462422 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}Quick pattern matchModerate context evalHistory analysisCross-reference stateMulti-step logicSemantic analysisGuidelinesObservationalSimple ActionablePreviously AppliedCustomer DependentJourney NodeDisambiguationLow Reasoning DepthMedium Reasoning DepthHigh Reasoning Depth

To sum it all up, if you use the same matching strategy for all guidelines, you either waste compute on simple cases or fail on complex ones.



### The Latency Challenge​


What made things truly hard for us for a long time (pun intended) was balancing two competing objectives: minimizing response latency while maintaining the agent's accuracy and consistency.


Nuanced reasoning takes time. Multiple LLM calls take time. Reasoning about dozens or even hundreds of guidelines takes a lot of time.


But customers expect quick responses. A 20 second delay while your agent "thinks" about which guidelines apply creates a terrible user experience. Well, that's where we were for a while, for several months, back in Parlant v1.0.


This is where our lead researcher, Bar Karov, came up with the idea of clearly differentiating between work that must happen before each response (hot path) and work that can happen while waiting for the customer's next input (async analysis).


Specifically, we could check whether a guideline was applied after the agent's response was sent, while the customer was reading it and composing their next message. This way, we could offload some of the reasoning work to this async phase, reducing the hot path latency significantly.


If we found that a guideline was indeed applied during this phase, we would then switch its next hot path matching call to a different, specialized prompt that assumes the guideline was applied. Both of the specialized hot path prompts worked much faster than the original one, which combined reasoning for both newly-matched and previously-applied guidelines.


MatchingAgentCustomer#mermaid-svg-99243{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;fill:#000000;}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#mermaid-svg-99243 .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#mermaid-svg-99243 .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#mermaid-svg-99243 .error-icon{fill:#552222;}#mermaid-svg-99243 .error-text{fill:#552222;stroke:#552222;}#mermaid-svg-99243 .edge-thickness-normal{stroke-width:1px;}#mermaid-svg-99243 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-svg-99243 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-svg-99243 .edge-thickness-invisible{stroke-width:0;fill:none;}#mermaid-svg-99243 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-svg-99243 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-svg-99243 .marker{fill:#666;stroke:#666;}#mermaid-svg-99243 .marker.cross{stroke:#666;}#mermaid-svg-99243 svg{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;}#mermaid-svg-99243 p{margin:0;}#mermaid-svg-99243 .actor{stroke:hsl(0, 0%, 83%);fill:#eee;}#mermaid-svg-99243 text.actor>tspan{fill:#333;stroke:none;}#mermaid-svg-99243 .actor-line{stroke:hsl(0, 0%, 83%);}#mermaid-svg-99243 .messageLine0{stroke-width:1.5;stroke-dasharray:none;stroke:#333;}#mermaid-svg-99243 .messageLine1{stroke-width:1.5;stroke-dasharray:2,2;stroke:#333;}#mermaid-svg-99243 #arrowhead path{fill:#333;stroke:#333;}#mermaid-svg-99243 .sequenceNumber{fill:white;}#mermaid-svg-99243 #sequencenumber{fill:#333;}#mermaid-svg-99243 #crosshead path{fill:#333;stroke:#333;}#mermaid-svg-99243 .messageText{fill:#333;stroke:none;}#mermaid-svg-99243 .labelBox{stroke:hsl(0, 0%, 83%);fill:#eee;}#mermaid-svg-99243 .labelText,#mermaid-svg-99243 .labelText>tspan{fill:#333;stroke:none;}#mermaid-svg-99243 .loopText,#mermaid-svg-99243 .loopText>tspan{fill:#333;stroke:none;}#mermaid-svg-99243 .loopLine{stroke-width:2px;stroke-dasharray:2,2;stroke:hsl(0, 0%, 83%);fill:hsl(0, 0%, 83%);}#mermaid-svg-99243 .note{stroke:#999;fill:#666;}#mermaid-svg-99243 .noteText,#mermaid-svg-99243 .noteText>tspan{fill:#fff;stroke:none;}#mermaid-svg-99243 .activation0{fill:#f4f4f4;stroke:#666;}#mermaid-svg-99243 .activation1{fill:#f4f4f4;stroke:#666;}#mermaid-svg-99243 .activation2{fill:#f4f4f4;stroke:#666;}#mermaid-svg-99243 .actorPopupMenu{position:absolute;}#mermaid-svg-99243 .actorPopupMenuPanel{position:absolute;fill:#eee;box-shadow:0px 8px 16px 0px rgba(0,0,0,0.2);filter:drop-shadow(3px 5px 2px rgb(0 0 0 / 0.4));}#mermaid-svg-99243 .actor-man line{stroke:hsl(0, 0%, 83%);fill:#eee;}#mermaid-svg-99243 .actor-man circle,#mermaid-svg-99243 line{stroke:hsl(0, 0%, 83%);fill:#eee;stroke-width:2px;}#mermaid-svg-99243 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}Hot pathAnalysis switches applied guidelines to a different optimized prompt on next hot path matching callMessage arrivesWhat guidelines apply?[Matched guidelines]Response[Response analysis: applied guidelines]

This architecture cut the matching time by more than half. It's the one we've been using since, and it maintains fast response times while still performing comprehensive and accurate guideline matching.



## The Cost Challenge​


Like I said, in many customer-facing use cases, compliance is non-negotiable. By this point, I've hopefully demonstrated the following points sufficiently:


- Dynamic guideline matching is essential for reliable agent behavior (again, see my previous post for more on this).
- Guideline matching is a complex task that requires nuanced reasoning, and consequently LLMs.
- This complexity leads to high latency and cost if not managed carefully.


Using parallelization and multi-stage analysis, we've managed to get response latencies down to acceptable levels (1-3 seconds on average, depending on the agent's complexity and the model used).


But making 10-20 LLM calls per response can get expensive, especially when using larger models. To tackle the cost issue, what we need to do it reduce the number of guidelines we evaluate deeply (using LLMs).


In well-designed Parlant agents, most guidelines will be scoped to specific customer journeys. This means that if a journey isn't active, its related guidelines shouldn't be evaluated at all. So if we first identified the relevant journeys, and only then evaluated the guidelines of the active journeys, we could significantly reduce the number of guidelines we needed to consider—especially when most times only one journey is active at a time.


MatcherEngine#mermaid-svg-8663541{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;fill:#000000;}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#mermaid-svg-8663541 .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#mermaid-svg-8663541 .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#mermaid-svg-8663541 .error-icon{fill:#552222;}#mermaid-svg-8663541 .error-text{fill:#552222;stroke:#552222;}#mermaid-svg-8663541 .edge-thickness-normal{stroke-width:1px;}#mermaid-svg-8663541 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-svg-8663541 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-svg-8663541 .edge-thickness-invisible{stroke-width:0;fill:none;}#mermaid-svg-8663541 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-svg-8663541 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-svg-8663541 .marker{fill:#666;stroke:#666;}#mermaid-svg-8663541 .marker.cross{stroke:#666;}#mermaid-svg-8663541 svg{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;}#mermaid-svg-8663541 p{margin:0;}#mermaid-svg-8663541 .actor{stroke:hsl(0, 0%, 83%);fill:#eee;}#mermaid-svg-8663541 text.actor>tspan{fill:#333;stroke:none;}#mermaid-svg-8663541 .actor-line{stroke:hsl(0, 0%, 83%);}#mermaid-svg-8663541 .messageLine0{stroke-width:1.5;stroke-dasharray:none;stroke:#333;}#mermaid-svg-8663541 .messageLine1{stroke-width:1.5;stroke-dasharray:2,2;stroke:#333;}#mermaid-svg-8663541 #arrowhead path{fill:#333;stroke:#333;}#mermaid-svg-8663541 .sequenceNumber{fill:white;}#mermaid-svg-8663541 #sequencenumber{fill:#333;}#mermaid-svg-8663541 #crosshead path{fill:#333;stroke:#333;}#mermaid-svg-8663541 .messageText{fill:#333;stroke:none;}#mermaid-svg-8663541 .labelBox{stroke:hsl(0, 0%, 83%);fill:#eee;}#mermaid-svg-8663541 .labelText,#mermaid-svg-8663541 .labelText>tspan{fill:#333;stroke:none;}#mermaid-svg-8663541 .loopText,#mermaid-svg-8663541 .loopText>tspan{fill:#333;stroke:none;}#mermaid-svg-8663541 .loopLine{stroke-width:2px;stroke-dasharray:2,2;stroke:hsl(0, 0%, 83%);fill:hsl(0, 0%, 83%);}#mermaid-svg-8663541 .note{stroke:#999;fill:#666;}#mermaid-svg-8663541 .noteText,#mermaid-svg-8663541 .noteText>tspan{fill:#fff;stroke:none;}#mermaid-svg-8663541 .activation0{fill:#f4f4f4;stroke:#666;}#mermaid-svg-8663541 .activation1{fill:#f4f4f4;stroke:#666;}#mermaid-svg-8663541 .activation2{fill:#f4f4f4;stroke:#666;}#mermaid-svg-8663541 .actorPopupMenu{position:absolute;}#mermaid-svg-8663541 .actorPopupMenuPanel{position:absolute;fill:#eee;box-shadow:0px 8px 16px 0px rgba(0,0,0,0.2);filter:drop-shadow(3px 5px 2px rgb(0 0 0 / 0.4));}#mermaid-svg-8663541 .actor-man line{stroke:hsl(0, 0%, 83%);fill:#eee;}#mermaid-svg-8663541 .actor-man circle,#mermaid-svg-8663541 line{stroke:hsl(0, 0%, 83%);fill:#eee;stroke-width:2px;}#mermaid-svg-8663541 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}Customer message arrivesStage 1: Parallel EvaluationStage 2: Journey-Scoped EvaluationCombine all matched guidelinesand generate responseMatch journey conditionsMatch global actionable guidelinesActivated journeysMatched global guidelinesMatch journey-scoped guidelinesMatched scoped guidelines

This works great at reducing cost, but this 2-stage process introduces latency again. To solve this, we added predictive journey relevance ranking as a first step. We essentially predict the top 3 journeys that we think will be activated, and speculatively evaluate their scoped guidelines in parallel with other hot path work, avoiding the added latency of the second stage—most of the time.



### Parallel Execution​


When we parallelize guideline matching, we do so in the form of batching. Each batch corresponds to a specific guideline category, and we process all batches concurrently. So we may have, say, 1 to 5 guidelines per batch, per category.


But batch size is a trade-off that varies between use cases. It controls a latency vs. cost tradeoff: larger batches mean fewer LLM calls (lower cost) but higher latency (due to more completion tokens), while smaller batches mean more LLM calls (higher cost) but lower latency.


So we've made batch size configurable via an OptimizationPolicy which can be overriden using the configure_container parameter when initializing the server. Each requests to the policy comes with a batch type hint, telling you what kind of batch is being created, so you can optimize accordingly:



```
class OptimizationPolicy(ABC):    @abstractmethod    def get_guideline_matching_batch_size(        self,        guideline_count: int,        hints: Mapping[str, Any] = {},    ) -> int:        ...
```



### Relational Resolution​


Once we started working with higher complexities with some of our users, we started seeing their difficulty in scoping guidelines correctly. Very quickly, you get two guidelines that conflict with each other in unexpected ways—and it can often be tricky to isolate the phrasing and fix the agent's behavior.


This is just the complexity of real-world semantics.


To solve this, we introduced Guideline Relationships, which allow designers to explicitly define relationships between guidelines, such as dependencies, mutual exclusions, etc.


This is an important feature of Parlant that allows agent designers to create complex semantics such as, "When this guideline matches, exclude that other guideline (do not apply it) even if it happened to match too," or, "This guideline should only be applied if that other guideline also matched," and so on.


The matching engine must then account for these relationships. We therefore load related guidelines that may not have matched directly but should be included due to entailment relationships and perform other such resolutions (priorities, mutual exclusion, dependencies, etc.) to ensure that the final result is truly aligned to the developer's intent.


Here's the complete flow:


#mermaid-svg-7358697{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;fill:#000000;}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#mermaid-svg-7358697 .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#mermaid-svg-7358697 .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#mermaid-svg-7358697 .error-icon{fill:#552222;}#mermaid-svg-7358697 .error-text{fill:#552222;stroke:#552222;}#mermaid-svg-7358697 .edge-thickness-normal{stroke-width:1px;}#mermaid-svg-7358697 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-svg-7358697 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-svg-7358697 .edge-thickness-invisible{stroke-width:0;fill:none;}#mermaid-svg-7358697 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-svg-7358697 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-svg-7358697 .marker{fill:#666;stroke:#666;}#mermaid-svg-7358697 .marker.cross{stroke:#666;}#mermaid-svg-7358697 svg{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;}#mermaid-svg-7358697 p{margin:0;}#mermaid-svg-7358697 .label{font-family:"trebuchet ms",verdana,arial,sans-serif;color:#000000;}#mermaid-svg-7358697 .cluster-label text{fill:#333;}#mermaid-svg-7358697 .cluster-label span{color:#333;}#mermaid-svg-7358697 .cluster-label span p{background-color:transparent;}#mermaid-svg-7358697 .label text,#mermaid-svg-7358697 span{fill:#000000;color:#000000;}#mermaid-svg-7358697 .node rect,#mermaid-svg-7358697 .node circle,#mermaid-svg-7358697 .node ellipse,#mermaid-svg-7358697 .node polygon,#mermaid-svg-7358697 .node path{fill:#eee;stroke:#999;stroke-width:1px;}#mermaid-svg-7358697 .rough-node .label text,#mermaid-svg-7358697 .node .label text,#mermaid-svg-7358697 .image-shape .label,#mermaid-svg-7358697 .icon-shape .label{text-anchor:middle;}#mermaid-svg-7358697 .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#mermaid-svg-7358697 .rough-node .label,#mermaid-svg-7358697 .node .label,#mermaid-svg-7358697 .image-shape .label,#mermaid-svg-7358697 .icon-shape .label{text-align:center;}#mermaid-svg-7358697 .node.clickable{cursor:pointer;}#mermaid-svg-7358697 .root .anchor path{fill:#666!important;stroke-width:0;stroke:#666;}#mermaid-svg-7358697 .arrowheadPath{fill:#333333;}#mermaid-svg-7358697 .edgePath .path{stroke:#666;stroke-width:2.0px;}#mermaid-svg-7358697 .flowchart-link{stroke:#666;fill:none;}#mermaid-svg-7358697 .edgeLabel{background-color:white;text-align:center;}#mermaid-svg-7358697 .edgeLabel p{background-color:white;}#mermaid-svg-7358697 .edgeLabel rect{opacity:0.5;background-color:white;fill:white;}#mermaid-svg-7358697 .labelBkg{background-color:rgba(255, 255, 255, 0.5);}#mermaid-svg-7358697 .cluster rect{fill:hsl(0, 0%, 98.9215686275%);stroke:#707070;stroke-width:1px;}#mermaid-svg-7358697 .cluster text{fill:#333;}#mermaid-svg-7358697 .cluster span{color:#333;}#mermaid-svg-7358697 div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:12px;background:hsl(-160, 0%, 93.3333333333%);border:1px solid #707070;border-radius:2px;pointer-events:none;z-index:100;}#mermaid-svg-7358697 .flowchartTitleText{text-anchor:middle;font-size:18px;fill:#000000;}#mermaid-svg-7358697 rect.text{fill:none;stroke-width:0;}#mermaid-svg-7358697 .icon-shape,#mermaid-svg-7358697 .image-shape{background-color:white;text-align:center;}#mermaid-svg-7358697 .icon-shape p,#mermaid-svg-7358697 .image-shape p{background-color:white;padding:2px;}#mermaid-svg-7358697 .icon-shape rect,#mermaid-svg-7358697 .image-shape rect{opacity:0.5;background-color:white;fill:white;}#mermaid-svg-7358697 .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#mermaid-svg-7358697 .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#mermaid-svg-7358697 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}EmbeddingsHigh-Probability Guideline CandidatesBatchesMatched GuidelinesNew Customer MessageStage 1: Journey PredictionStage 2: Guideline PruningStage 3: Categorize and Batch GuidelinesStage 4: Parallel MatchingStage 5: Relational ResolutionFinal Guideline Set


### The Preparation Iteration Loop​


Now it gets more fun... sort of!


Guideline matching can't always be a one-shot process, even when sending a single response.


Why? Because tool calls return new information during response processing, and this new information might trigger additional guidelines that affects the agent's behavior and the response message the customer ends up seeing.


We therefore need to prepare all of the required context before the agent is ready to come out with its fully-aligned response, according to its configuration.


Example scenario (banking agent):


In this case, the agent is configured to offer investment options for customers with more than $10,000 in their checking account. We expect this to happen every time the customer's checking account balance comes up during the conversation, which bridges gracefully into the upsell offer, without being too pushy.


1. Iteration 1: Customer says "How much money do I have in my checking account?"

Guideline matches: "Customer asks for account information"
Tool called: get_account_info()
Result: {..., "balance": "$1,200"}
2. Iteration 2: Now we know the customer's balance

New guideline matches: "If you find that their checking account balance is over $10,000, recommend investment options"
Tool called: get_investment_options()
Result: Investment options details
3. Iteration 3: We have all the information needed

New guidelines matching based on investment options? No.
Ready to respond with a fully-aligned answer!


So when tools are involved, we need to reevaluate relevant result-affected guidelines until we reach a stable state, where we're sure all relevant guidelines have been matched.


Importantly, to control cost and latency, we only evaluate guidelines that could be affected by the new information returned from tool calls. This relationship is configurable using the SDK.


Here's an illustration of this iterative process as it's built into the engine:



ToolsMatchingEngineCustomer#mermaid-svg-8283799{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;fill:#000000;}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#mermaid-svg-8283799 .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#mermaid-svg-8283799 .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#mermaid-svg-8283799 .error-icon{fill:#552222;}#mermaid-svg-8283799 .error-text{fill:#552222;stroke:#552222;}#mermaid-svg-8283799 .edge-thickness-normal{stroke-width:1px;}#mermaid-svg-8283799 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-svg-8283799 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-svg-8283799 .edge-thickness-invisible{stroke-width:0;fill:none;}#mermaid-svg-8283799 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-svg-8283799 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-svg-8283799 .marker{fill:#666;stroke:#666;}#mermaid-svg-8283799 .marker.cross{stroke:#666;}#mermaid-svg-8283799 svg{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;}#mermaid-svg-8283799 p{margin:0;}#mermaid-svg-8283799 .actor{stroke:hsl(0, 0%, 83%);fill:#eee;}#mermaid-svg-8283799 text.actor>tspan{fill:#333;stroke:none;}#mermaid-svg-8283799 .actor-line{stroke:hsl(0, 0%, 83%);}#mermaid-svg-8283799 .messageLine0{stroke-width:1.5;stroke-dasharray:none;stroke:#333;}#mermaid-svg-8283799 .messageLine1{stroke-width:1.5;stroke-dasharray:2,2;stroke:#333;}#mermaid-svg-8283799 #arrowhead path{fill:#333;stroke:#333;}#mermaid-svg-8283799 .sequenceNumber{fill:white;}#mermaid-svg-8283799 #sequencenumber{fill:#333;}#mermaid-svg-8283799 #crosshead path{fill:#333;stroke:#333;}#mermaid-svg-8283799 .messageText{fill:#333;stroke:none;}#mermaid-svg-8283799 .labelBox{stroke:hsl(0, 0%, 83%);fill:#eee;}#mermaid-svg-8283799 .labelText,#mermaid-svg-8283799 .labelText>tspan{fill:#333;stroke:none;}#mermaid-svg-8283799 .loopText,#mermaid-svg-8283799 .loopText>tspan{fill:#333;stroke:none;}#mermaid-svg-8283799 .loopLine{stroke-width:2px;stroke-dasharray:2,2;stroke:hsl(0, 0%, 83%);fill:hsl(0, 0%, 83%);}#mermaid-svg-8283799 .note{stroke:#999;fill:#666;}#mermaid-svg-8283799 .noteText,#mermaid-svg-8283799 .noteText>tspan{fill:#fff;stroke:none;}#mermaid-svg-8283799 .activation0{fill:#f4f4f4;stroke:#666;}#mermaid-svg-8283799 .activation1{fill:#f4f4f4;stroke:#666;}#mermaid-svg-8283799 .activation2{fill:#f4f4f4;stroke:#666;}#mermaid-svg-8283799 .actorPopupMenu{position:absolute;}#mermaid-svg-8283799 .actorPopupMenuPanel{position:absolute;fill:#eee;box-shadow:0px 8px 16px 0px rgba(0,0,0,0.2);filter:drop-shadow(3px 5px 2px rgb(0 0 0 / 0.4));}#mermaid-svg-8283799 .actor-man line{stroke:hsl(0, 0%, 83%);fill:#eee;}#mermaid-svg-8283799 .actor-man circle,#mermaid-svg-8283799 line{stroke:hsl(0, 0%, 83%);fill:#eee;stroke-width:2px;}#mermaid-svg-8283799 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}Iteration 1Iteration 2Iteration 3Prepared to respond"Upgrade my plan"Match guidelines[Check current plan]get_current_plan()"Basic"Re-match with plan context[Recommend Premium]get_plan_comparison()Premium detailsRe-match with comparisonNo new guidelinesPersonalized recommendation


### Pre-Evaluation and Optimization​


Since we know that different guideline categories need different matching strategies, how (and more importantly, when) do we determine which strategy to use for each guideline?


This is where evaluations come in. When you add a guideline to Parlant for the first time (i.e., the first you're running your agent since the guideline's addition), Parlant analyzes it immediately to determine its preferred matching strategy.



```
# Guideline metadata includes strategy hintsguideline = await agent.create_guideline(    condition="The customer is a VIP member",    action="Offer complimentary priority shipping")# Parlant internally marks this as "customer_dependent"# Future matching uses the optimized strategy for that category
```


![Evaluation of the agent configuration](https://www.parlant.io/img/example-evaluation.gif)



This pre-evaluation allows us to completely avoid any runtime overhead for strategy selection. The system already knows which specialized batch and prompts to use for each guideline. We also cache these evaluations so that subsequent restarts of the agent don't require re-evaluation of unmodified guidelines.



## Attentive Reasoning Queries (ARQs)​


We've established that different guideline categories need specialized reasoning. Now let's talk about how that reasoning is structured, because—let me tell you—Chain-of-Thought and off-the-shelf reasoning models provided nothing close to the reliability we needed to guarantee with Parlant


How did we know it wasn't good enough? Because our comprehensive test suite didn't pass anywhere near consistently enough with them. Incidentally, this test suite tells us the real story about any new model launch (despite any benchmark claims), which is why we're also so pedantic on which models Parlant uses under the hood with different providers.



### What Are ARQs?​


Attentive Reasoning Queries (ARQs) are a novel prompting technique developed for Parlant by our research team, specifically for instruction-following accuracy.


They basically leverage and combine two things:


1. They rely on an LLM API's ability to generate structured outputs (normally, through constrained decoding), which means we can tightly control what gets generated first.
2. This control of what goes first allows us to take advantage of the recency bias of LLMs: the most recently presented information has a stronger influence on the output.


Here's how it works, very briefly.


Rather than asking an LLM to reason freely before generating the required output (as in CoT), we provide use-case-specific, systematic reasoning steps with targeted queries that reinstate critical instructions and information from the prompt throughout the process, and provide the required output immediately after "recalling" this high-signal information into the end of the context window, where attention is most focused.


For example, here's a basic ARQ-based completion schema for classifying some inputs (you can do this multiple times throughout the same completion schema):


Chain-of-Thought:



```
Reason about inputs X and Y...<END_OF_REASONING_TOKEN>{    "classification_for_input_x": "<BOOL>",    "classification_for_input_y": "<BOOL>"}
```


Attentive Reasoning Queries:



```
{    "notes_about_input_x": "<FILL THIS OUT>",    "instructions_regarding_input_x": "<FILL THIS OUT>",    "reasoning_about_input_x": "<FILL THIS OUT>",    "classification_for_input_x": "<BOOL>",    "notes_about_input_y": "<FILL THIS OUT>",    "instructions_regarding_input_y": "<FILL THIS OUT>",    "reasoning_about_input_y": "<FILL THIS OUT>",    "classification_for_input_y": "<BOOL>"}
```


In this way, the structure allows us to ensure that:


1. We reason about a classification choice (or any other type of output) right before generating it. The recency bias improves the classification's accuracy when it immediately follows the reasoning.
2. The reasoning itself immediately follows the reinstatement of notes and instructions regarding the input, improving the reasoning's accuracy and completeness.


Our research paper on ARQs showed compelling results: a 90.2% success rate across 87 test scenarios in Parlant; it significantly outperformed Chain-of-Thought reasoning (86.1%) and far exceeded direct response generation (81.5%); and it was particularly strong at guideline re-application and hallucination prevention.


You can review the full paper we published on arxiv: Attentive Reasoning Queries on arxiv.org



### ARQs Per Guideline Category​


We carefully tuned the ARQ-based reasoning schemas for each guideline category, optimizing for both accuracy and latency (in that order).


These schemas (coded using Pydantic models) define the exact order and content of the queries. Let me touch on a couple of examples from Parlant's codebase.



#### Observational Guidelines​


The ARQ structure is defined by this Pydantic schema from observational_batch.py:



```
class GenericObservationalGuidelineMatchSchema(DefaultBaseModel):    guideline_id: str    condition: str    rationale: str    applies: bool
```


Note that the order of fields matters! The LLM must generate each field in sequence:


1. guideline_id and condition: First, the LLM "recalls" which specific guideline is being evaluated by restating its ID and condition. This leverages recency bias: the information is now at the top of the model's attention.
2. rationale: Next, the LLM must reason about whether the condition is met, providing specific evidence from the conversation. Because the condition was just restated, attention is focused on it.
3. applies: Finally, the LLM outputs the boolean decision, immediately following the reasoning. The recency of the rationale ensures the decision is grounded in the just-completed analysis.


Example output for condition="The customer mentioned a discount code":



```
{  "guideline_id": "3",  "condition": "The customer mentioned a discount code",  "rationale": "The customer stated a discount code (SAVE20)",  "applies": true}
```


This sequential structure prevents the LLM from making snap decisions based on semantic similarity alone. It must explicitly reason first.



#### Previously Applied Actionable Guidelines​


These guidelines have already been followed once in the conversation. Should they apply again? Remember, we're looking for a robust and consistent solution.


To consistently pass our comprehensive test suite (rather than a few simple demo cases), here's the ARQ set we've optimized over time:


It's defined by this schema from guideline_previously_applied_actionable_batch.py:



```
class GenericPreviouslyAppliedActionableBatch(DefaultBaseModel):    guideline_id: str    condition: str    action: str    condition_met_again: bool    action_wasnt_taken: Optional[bool] = None    should_reapply: bool
```


The sequential reasoning enforced by this schema:


1. guideline_id, condition, action: Recall the guideline being evaluated: both its condition and its action.
2. condition_met_again: Evaluate whether the condition that originally triggered this guideline is met again in the current context. This forces explicit temporal reasoning.
3. action_wasnt_taken: If the condition is met again, determine if the action wasn't yet taken in this new context. This step is optional (nullable) because if the condition isn't met again, this question is irrelevant.
4. should_reapply: Final decision about re-application, made after explicitly reasoning about context shifts.


Example for condition="The customer wants to return an item", action="Explain the 30-day return policy and ask for their order number":



```
{  "guideline_id": "3",  "condition": "The customer wants to return an item",  "action": "Ask for their order number",  "condition_met_again": true,  "action_wasnt_taken": true,  "should_reapply": true}
```


Here, the customer may have mentioned returns again, but regarding a different item, so we must ask for the order number again.


When we didn't have this ARQ structure, even the best LLMs would often say "no, don't reapply" or "yes, reapply" without proper reasoning, leading to inconsistent behavior.



## But Is All of This Really Necessary?​


We have a very comprehensive test suite. Parlant was built from the ground up with test-driven development. We have hundreds of unit tests that define what correct behavior looks like.


Most importantly, we did start out with very simple implementations that seemed like they should work (as I've touched on in the beginning of this post). They just failed too many tests in our suite, too frequently.


Yet the whole point with Parlant is to enable truly reliable and compliant conversations, so passing the test suite wasn't an option. Of course, if you don't require reliability with your agents, you should probably use a different solution. But if you do, we're basically working our butts off to provide a truly accurate and scalable solution that you can trust to put in front of your customers in large-scale production deployments.


As Parlant's open-source, our research and innovations will continue to be open for everyone to build upon, we continually find further ways to optimize and improve in every dimension, so that compliant agents can be achieved through an elegant, maintainable, and easy to control interface.


Here are a few real test scenarios from Parlant's BDD test suite:



### Test Suite Examples​


To give you a sense of the kinds of scenarios we cover, here are some real tests from our suite that validate critical aspects of guideline matching.


Note that these tests aren't vague. We don't score "friendliness" or "helpfulness." These are concrete, binary correctness tests that validate specific reasoning capabilities of the guideline matching system.


In other words, we didn't build them to fool ourselves with fuzzy metrics, but rather to provide a clear mirror to help us ensure that the agent behaves correctly in well-defined, critical scenarios.


We've validated our guideline matching techniques across multiple LLM providers, including OpenAI (GPT-4* series), Anthropic (Claude Sonnet 3 and up), Google (Gemini Flash 2.5, and Llama 3.*).


Performance varies by model. All medium-to-large models do quite well, but not all perform equally. OpenAI's models tend to be the most consistent throughout the test suite, while Llama 3.* models have curiously done better at some of the harder tasks.


Our testing process is the reason why we're somewhat selective about which models Parlant uses by default for different operations, with different providers.


Now, because Parlant is open-source, development teams can run the full test suite with their preferred LLM provider to verify compatibility. If you're considering using Parlant with a specific model (like Cohere Command R+ or others), you can validate its performance with your agent's requirements by running the tests yourself.


This transparency allows you to make informed decisions about which LLMs to use, and even switch providers if needed while maintaining confidence in Parlant's reliability.


Let's look at a few examples from our BDD test suite.



#### Needle in a Haystack​


This test validates that the guideline matching system can find the 1 relevant guideline among 51 total guidelines without false positives.



```
Scenario: The agent finds and follows relevant guidelines like a needle in a haystack    Given an agent    And an empty session    And a customer message, "I'm thirsty"    And a guideline to offer thirsty customers a Pepsi when the customer is thirsty    And 50 other random guidelines    When processing is triggered    Then a single message event is emitted    And the message contains an offering of a Pepsi
```


Naive approaches that rely purely on semantic similarity or don't properly filter guidelines will fail this test by either missing the relevant guideline entirely (false negatives), obfuscating the LLM's instructions by including irrelevant guidelines in the context (false positives), or simply taking too long to process.



#### Journey Backtracking Based on Context Shifts​



```
Scenario: Journey returns to earlier step when the conversation justifies doing so    Given an agent    And the journey called "Book Taxi Ride"    And a journey path "[2, 3, 4]" for the journey "Book Taxi Ride"    And a customer message, "Hi, I'd like to book a taxi for myself"    And an agent message, "Great! What's your pickup location?"    And a customer message, "Main street 1234"    And an agent message, "Got it. What's your drop-off location?"    And a customer message, "3rd Avenue by the river"    And an agent message, "Got it. What time would you like to pick up?"    And a customer message, "Oh hold up, my plans have changed. I'm actually going to need a cab for my son, he'll be waiting at JFK airport, at the taxi stand."    When processing is triggered    Then a single message event is emitted    And the message contains asking the customer for the drop-off location
```


This test validates intelligent journey state reasoning: The customer's new information invalidates previously collected pickup location, requiring the system to backtrack to step 2 (pickup location) rather than continuing to step 5.



#### Nuanced Condition Evaluation with Agent Intention​



```
Scenario: The agent ignores a matched agent intention guideline when it doesn't intend to do its condition    Given an agent    And an empty session    Given a guideline to remind that we have a special sale if they book today when you recommend flight options    Given a guideline to suggest only ground based travel options when the customer asks about travel options    And a customer message, "Hi, I want to go to California from New york next week. What are my options?"    When processing is triggered    Then a single message event is emitted    And the message contains a suggestion to travel with bus or train    And the message contains no flight option    And the message contains no sale option
```


This test validates that the system correctly understands the first guideline's condition includes "when you recommend flight options" as a prerequisite. Since the second guideline explicitly says "suggest only ground-based travel," the agent won't be recommending flights, so the first guideline shouldn't match.


This requires semantic understanding and prediction of probable agent intentions within guideline conditions—another thing I've yet to touch on in the implementation details, but which Parlant also performs.



### Continuous Performance Improvement​


Parlant's test suite spans over more than 1,000 unique tests covering a wide range of guideline matching scenarios, including edge cases and complex interactions.


Every component of the guideline matching system exists because removing it breaks specific tests.


In these, we ensure:


- Consistent handling of temporal reasoning edge cases
- Reliable prevention of repetitive or inappropriate guideline reapplication
- Accurate journey progression through complex multi-step flows


To wrap it all up, here's how we got here:


- Phase 1: Started with naive implementations (e.g., embeddings)
- Phase 2: Added simple LLM-based matching
- Phase 3: Introduced categorization and specialized strategies
- Phase 4: Developed ARQs for each category
- Phase 5: Optimized with multi-stage pipeline and parallel processing


Each phase was driven by test failures showing us exactly where the system was breaking.



## The Big Picture​


Let's zoom back out. Parlant guidelines are, after all, conceptually simple:



```
await agent.create_guideline(    condition="Customer asks about returns",    action="Explain our 30-day return policy")
```


But making that simple concept work reliably in the chaotic reality of human conversation—as you can now see—takes a lot of fairly sophisticated engineering under the hood.


That's what we mean when we say Parlant does the heavy-lifting for you so that you can focus on a simple declarative interface for defining your agent's behavior, while addressing the complexities of real-world customer interactions.



#### Parlant's Philosophy​


We fundamentally believe the feedback cycle of building agents, across all stakeholders, should be simple. Business experts should be able to say: "When this happens, the agent should do that".


And a developer should be able to implement it in minutes—and have it work reliably—every time, in every context, across millions of conversations.


To recap, here's what we've designed and implemented over time to make this a reality:


- Optimized matching strategies per category
- Automatic categorization of guideline types
- Multi-stage pipeline with filtering and batching
- Parallel processing for latency optimization
- ARQ-structured reasoning for consistency
- Iterative preparation loops for correct context assembly
- Extensive test coverage to catch edge cases


In doing so, we've built a system that uses declarative guidelines reliably, while it avoids:


- Brittle prompt engineering where one change breaks five other things.
- Bespoke, rigid graphs and decision trees that can't handle natural conversation flow.


That's what guideline matching enables, and why we think it's worth investing in its complexity. I hope that you do too!



## The Road Ahead​


Guideline matching is at the core of Parlant, and we're continuously improving it.


Here are the main areas of active research and development:


- Further latency reduction using fine-tuned, small language models.
- Cost reduction using first-pass filtering with tiny models, so that far fewer guidelines actually need to go through the full matching process.
- Programmatic matching for certain guideline types, where we can use deterministic logic instead of LLM reasoning.


Everything we've discussed is visible in the Parlant repository.


Explore the implementation:


- Engine: /src/parlant/core/engines/alpha/engine.py
- Guideline matching: /src/parlant/core/engines/alpha/guideline_matching/
- Strategies: guideline_matching/generic/
- Tests: /tests/


You can track improvements through GitHub issues and pull requests.


Very, very importantly, we always welcome and are excited about community input!



### Be a Part of the Vision​


Building reliable customer-facing conversational AI is a hard problem—unlike what they say... While we're not claiming to have solved it perfectly (we're getting there), we've made significant progress, and we're sharing that progress openly. And I think it's fair to say we're currently leading the way in this space.


If you're building conversational agents, you'll encounter these challenges. Understanding guideline matching more deeply helps you make informed architectural choices, whether you use Parlant, build your own solution, or hybrid both approaches.


Lastly, I want to thank Alex Shtoff for reviewing the post, and helping to flesh it out, make it clearer, more palatable, and more useful.


Get involved:


- Read the documentation
- Join the Discord community
- Examine the source code
- Share feedback and contribute improvements


[Questions about guideline matching?](https://discord.gg/duxWqxKk6J)

---


Have you built similar systems? We'd love to hear about your experiences and challenges. Reach out on Discord or via GitHub.

Share post:[](https://www.linkedin.com/shareArticle?mini=true&url=https://www.parlant.io/blog/inside-parlant-guideline-matching-engine/&text=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io)[](https://twitter.com/intent/tweet?url=https://www.parlant.io/blog/inside-parlant-guideline-matching-engine/&text=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io)[](https://www.facebook.com/sharer/sharer.php?u=https://www.parlant.io/blog/inside-parlant-guideline-matching-engine/)[](https://www.reddit.com/submit?url=https://www.parlant.io/blog/inside-parlant-guideline-matching-engine/&title=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io)[](https://bsky.app/intent/compose?text=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io%20%20https%3A%2F%2Fwww.parlant.io%2Fblog%2Finside-parlant-guideline-matching-engine%2F)Tags:parlantguideline-matchingconversational-aiarqsllm-alignment
