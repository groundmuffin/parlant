---
title: "Parlant vs DSPy"
date: "October 1, 2025"
author: "Yam Marcovitz"
source: "https://www.parlant.io/blog/parlant-vs-dspy"
---

[](https://www.linkedin.com/in/yam-marcovic/)[Yam Marcovitz](https://www.linkedin.com/in/yam-marcovic/)Parlant vs DSPyOctober 1, 20258 min readSome interesting questions we've been getting lately: "Is Parlant like DSPy?" "What's the difference?" "Which one should I use?"


I get why people are confused about it. Both frameworks work with LLMs, both use Python, and both claim to make LLMs more consistent and effective. At the same time, though, they solve completely different problems.


Let's break it down.


- The Quick Answer
- What is DSPy?The Core Concept: Programming, Not PromptingWhat DSPy Excels AtWhat DSPy Doesn't Do
- What is Parlant?The Core Problem: Alignment at ScaleHow Parlant WorksWhat Parlant Excels AtWhat Parlant Doesn't Do
- The Key Differences
- When to Use WhichUse DSPy When:Use Parlant When:Use Both When:
- The Core Difference
- Making the Right Choice



## The Quick Answer​


DSPy is about optimizing how you get good outputs from language models through automated prompt engineering and model tuning. It's a bit like a compiler for LLM prompts.


Parlant is about controlling and aligning conversational agent behavior with business rules and compliance requirements. It's a framework for building customer-facing agents that actually follow your instructions and generate safe and consistent responses.


They're solving different problems. In fact, you could even use them together—but more on that later.



## What is DSPy?​


DSPy (Declarative Self-improving Python) came out of Stanford NLP and offers a different way to work with LLMs: Instead of manually crafting and tweaking prompts, you write declarative Python code that describes what you want the model to do, and DSPy figures out how to prompt the model to get it.



### The Core Concept: Programming, Not Prompting​


The driving assumption behind DSPy is that prompt engineering is brittle. You write a carefully crafted prompt, test it, tweak it, test it again. Then you switch models or change your task slightly, and everything breaks. You're back to square one.


DSPy says: stop doing that. Instead, write code that specifies your task's structure, and let DSPy automatically generate and optimize the prompts for you.



```
# DSPy approach - define your moduleclass SentimentClassifier(dspy.Module):    def __init__(self):        self.classify = dspy.ChainOfThought("text -> sentiment")    def forward(self, text):        return self.classify(text=text)# Provide input/output examples for DSPy to optimize withtrainset = [    dspy.Example(text="I love this product!", sentiment="positive").with_inputs("text"),    dspy.Example(text="Terrible experience.", sentiment="negative").with_inputs("text"),    dspy.Example(text="It's okay I guess.", sentiment="neutral").with_inputs("text"),    # ... more examples]# Define a metric to evaluate the quality of outputsdef sentiment_metric(gold, pred, trace=None):    return gold.sentiment == pred.sentiment# DSPy optimizes the underlying prompts automatically based on the examples and metricoptimizer = dspy.BootstrapFewShot(metric=sentiment_metric)optimized_classifier = optimizer.compile(SentimentClassifier(), trainset=trainset)# Now use the optimized classifierresult = optimized_classifier(text="This exceeded my expectations!")print(result.sentiment)  # Output: "positive"
```



### What DSPy Excels At​


DSPy is an awesome tool for:


- Optimizing model performance across different tasks and models
- Automating prompt engineering so you don't have to manually tweak prompts
- Building complex reasoning pipelines with multiple LLM calls
- Rapid experimentation with different model configurations
- RAG systems where you need to optimize retrieval and generation together



### What DSPy Doesn't Do​


DSPy isn't designed for:


- Enforcing a large and dynamic set of strict business rules in conversations
- Guaranteeing compliance with regulatory requirements
- Managing multi-turn conversational state and flow
- Preventing specific types of agent misbehavior
- Ensuring agents never say certain things (or always say others when required to)



## What is Parlant?​


Parlant is a conversational alignment engine built specifically for customer-facing AI agents that need to follow business rules consistently.



### The Core Problem: Alignment at Scale​


Parlant is driven by the following assumption: When building customer-facing agents, even when you get the LLM to produce "correct" outputs most of the time, you still have a massive problem. Agents still go off on tangents, ignore instructions, hallucinate information, breach business protocols, or just generally behave unpredictably.


The worst part is that traditional approaches to "fixing" this, like adding more instructions to your prompt, actually make it worse. Research shows that as you add more instructions, LLMs get worse at following them (see The Curse of Instructions).


Parlant solves this through dynamic context management and structured behavior modeling.



### How Parlant Works​


Instead of throwing all your instructions at the LLM at once, Parlant breaks them into granular, conditional guidelines and only loads the relevant ones for each conversation turn:



```
# Parlant approachawait agent.create_guideline(    condition="Customer asks about refunds",    action="First acknowledge their concern, then explain our 30-day refund policy")await agent.create_guideline(    condition="Customer has already declined an upgrade",    action="Do not mention upgrades again in this session")
```


The condition part is crucial. Parlant's guideline matcher evaluates which guidelines are relevant right now, loads only those into the LLM's context, and uses specialized prompting techniques (ARQs) to maximize conformance to the guidelines.


For multi-step interaction design, Parlant provides journeys:



```
journey = await agent.create_journey(    title="Handle Refund Request",    conditions=["Customer wants to return or refund an item"],    description="Guide customers through our refund process")first_step = await journey.initial_state.transition_to(    chat_state="Ask for order ID")second_step = await first_step.target.transition_to(    tool_state=load_order_details)third_step = await second_step.target.transition_to(    chat_state="Confirm you have the right order")# ... continue building the journey
```


Unlike rigid flowchart systems, Parlant journeys are adaptive; that is, the agent can skip steps, revisit states, or adapt to the customer's needs while maintaining the overall intended flow of the journey.



### What Parlant Excels At​


Parlant is built for:


- Customer-facing conversational agents that need predictable, compliant behavior
- Business rule enforcement at scale across millions of interactions
- Compliance-critical applications where unauthorized behavior creates liability
- Iterative behavior refinement as you learn what your agent needs to handle
- Multi-turn conversation management with complex state and context



### What Parlant Doesn't Do​


Parlant isn't designed for:


- Optimizing model performance across different providers
- Automated prompt tuning or hyperparameter optimization
- Non-conversational LLM tasks (classification, extraction, etc.)
- General-purpose LLM application building



## The Key Differences​


Let's break this down side by side:


AspectDSPyParlantPrimary GoalOptimize LLM outputs through automated prompt engineeringControl and align conversational agent behavior with business rulesCore InnovationTreats prompts as learnable parameters to be optimizedDynamic context management and conditional instruction loadingArchitectureDeclarative modules + optimizersAlignment model (guidelines, journeys, tools) + enforcement engineWhen Instructions ChangeRe-run optimizer to generate new promptsChanges take effect immediately, no retrainingTarget Use CaseAny LLM task (RAG, classification, QA, etc.)Customer-facing conversational agentsDeveloper ExperienceWrite modules, define metrics, run optimizersWrite guidelines and journeys as you discover needsModel RelationshipModel-agnostic optimization across providersModel-agnostic enforcement of business rulesCompliance FocusNot a primary concernCentral design principle

## When to Use Which​



### Use DSPy When:​


- You're building LLM applications that aren't primarily conversational
- You need to optimize performance across different models or tasks
- You're doing RAG and want to optimize retrieval + generation together
- You want to avoid manual prompt engineering
- Your main challenge is getting better outputs from the model



### Use Parlant When:​


- You're building customer-facing conversational agents
- You need strict adherence to business rules and compliance requirements
- Your agent must never say certain things or must always follow specific protocols
- You're iteratively refining agent behavior based on real-world interactions
- Your main challenge is controlling what the agent says and does



### Use Both When:​


Here's an interesting fact: Parlant and DSPy are complementary.


You could use DSPy to optimize specific components within your Parlant agent. For example:


- Use Parlant to structure the conversation and enforce business rules
- Use DSPy to optimize your retrieval pipeline for finding relevant information
- Use Parlant's tool system to call DSPy-optimized modules when needed



```
# Hypothetical example: DSPy-optimized retrieval in a Parlant tool@p.toolasync def find_policy_info(context: p.ToolContext, query: str) -> p.ToolResult:    # Use DSPy-optimized RAG pipeline    result = dspy_rag_pipeline(query)    return p.ToolResult(data=result)...# Parlant guideline controls when/how this tool is usedawait agent.create_guideline(    condition="Customer asks about a specific policy",    action="Answer based on the policy information you find",    tools=[find_policy_info])
```



## The Core Difference​


Perhaps the deepest difference is philosophical:


DSPy operates on the assumption that with the right prompts and optimization, you can get models to reliably produce what you want.


Parlant operates on the assumption that LLM behavior is always inherently uncertain and must be actively managed, filtered, and controlled at the architectural level. It's about structuring the conversation space so the agent can't go off the rails even when the model wants to.


Both assumptions are valid for different use cases.


If you're building a question-answering system where you just need accurate answers, DSPy's optimization approach works great.


If you're building a customer service agent where an unauthorized $10,000 refund would be catastrophic, you need Parlant's design and enforcement mechanisms.



## Making the Right Choice​


The confusion between Parlant and DSPy is understandable: they're both modern Python frameworks for working with LLMs. But understanding the difference comes down to this question:


What's your biggest challenge?


- "My model outputs aren't good enough" → DSPy
- "My agent doesn't follow my business rules consistently" → Parlant
- "I need both RAG optimization and conversational control" → Consider using both


So you don't have to choose just one paradigm. As the LLM application ecosystem matures, we're going to see more integration between optimization frameworks like DSPy and control frameworks like Parlant.


Building incredible LLM applications isn't about finding one perfect framework. Instead, it's about composing the right tools for your specific needs.


[Questions about Parlant?](https://discord.gg/duxWqxKk6J)

---


Have you tried both frameworks? I'd love to hear about your experience. Reach out on Discord or via our contact page.

Share post:[](https://www.linkedin.com/shareArticle?mini=true&url=https://www.parlant.io/blog/parlant-vs-dspy/&text=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io)[](https://twitter.com/intent/tweet?url=https://www.parlant.io/blog/parlant-vs-dspy/&text=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io)[](https://www.facebook.com/sharer/sharer.php?u=https://www.parlant.io/blog/parlant-vs-dspy/)[](https://www.reddit.com/submit?url=https://www.parlant.io/blog/parlant-vs-dspy/&title=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io)[](https://bsky.app/intent/compose?text=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io%20%20https%3A%2F%2Fwww.parlant.io%2Fblog%2Fparlant-vs-dspy%2F)Tags:parlantai-agentsdspyconversational-aialignment
