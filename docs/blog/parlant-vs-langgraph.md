---
title: "Parlant vs LangGraph"
date: "October 18, 2025"
author: "Yam Marcovitz"
source: "https://www.parlant.io/blog/parlant-vs-langgraph"
---

[](https://www.linkedin.com/in/yam-marcovic/)[Yam Marcovitz](https://www.linkedin.com/in/yam-marcovic/)Parlant vs LangGraphOctober 18, 202522 min readGet ready for a hardcore deep dive! The most asked-for framework comparison from the Parlant community is finally here.


"How is Parlant different from LangGraph?" "Can I use them together?" "Which one should I use for my AI agent and why?"


These are the great questions we've been getting from back when we launched Parlant v1.0. And the reason they're great is that they allow us to get right to the heart of what makes Parlant unique, why we even built it, and the surprising lessons we've learned building real-world conversational AI while working with truly large-scale clients.



#### Contents:​


- Introduction
- The Quick Answer
- Understanding LangGraph's ApproachCommon LangGraph PatternsWhat LangGraph Excels At
- The Problem with Router PatternsIsolated Specialization Is Inherently BrokenArticulating the Core Design Issue
- How Parlant Approaches Free-Form ConversationDynamic Guideline MatchingWhy This Works for Conversational CoherenceHow Parlant Keeps Accuracy Scalable
- When LangGraph Works Well for Conversational AI
- Using LangGraph and Parlant Together
- The Architectural Difference
- When to Use Which
- "Can't I Just Build This with LangGraph?"The Rabbit Hole Goes Deeper Than You ThinkLeverage Our Work & ResearchParlant is Fully Open Source
- Making the Right Choice



### Introduction​


When coders first approach building conversational agents, graph-based architectures like LangGraph feel intuitive and familiar. Router patterns and specialized nodes map cleanly to how we think about organizing functionality. This is why these patterns are so popular.


However, through years of studying and building production conversational systems, working with some of the top professionals in the field (shout out to CDI), we've discovered challenges that most developers aren't aware of when they start. These challenges aren't immediately obvious: they emerge gradually as your agent handles more conversations, more topics, and more complex user behaviors.


In this post, we'll demonstrate how router-based architectures inherently fail for natural, free-form conversation—not due to implementation details you can fix, but due to fundamental architectural constraints. Understanding these limitations now can save you from a complete rewrite later when you discover your graph-based system can't scale to handle the way users actually converse.


Let me break down the key differences, explain where LangGraph's common patterns create challenges for conversational AI, and show you why and how Parlant approaches these problems differently.



## The Quick Answer​


LangGraph is a framework for building agentic workflows through explicit graph-based orchestration. It excels at task decomposition, multi-step automation, and scenarios where you need precise control over execution flow.


Parlant is an AI alignment engine designed specifically for natural customer-facing dialogue. It's built to handle free-form conversations where users don't follow scripts: they mix topics freely, and expect coherent responses across multiple contexts simultaneously.


They solve different problems. Actually, they can work together—LangGraph can function as a lower-level orchestration framework triggered by a Parlant agent's tools for complex retrieval, action workflows, or specialized reasoning tasks.



## Understanding LangGraph's Approach​


LangGraph represents agentic applications as graphs where nodes are computational steps (LLM calls, tool invocations) and edges define control flow. This architecture is powerful for workflow automation and task orchestration.



### Common LangGraph Patterns​


The most popular patterns for building agents with LangGraph include:


1. Supervisor (Router) Pattern


A central coordinator (supervisor) routes requests to specialized agents based on the query type. Each specialized agent has its own system prompt optimized for a specific domain.


#mermaid-svg-8489929{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;fill:#000000;}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#mermaid-svg-8489929 .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#mermaid-svg-8489929 .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#mermaid-svg-8489929 .error-icon{fill:#552222;}#mermaid-svg-8489929 .error-text{fill:#552222;stroke:#552222;}#mermaid-svg-8489929 .edge-thickness-normal{stroke-width:1px;}#mermaid-svg-8489929 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-svg-8489929 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-svg-8489929 .edge-thickness-invisible{stroke-width:0;fill:none;}#mermaid-svg-8489929 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-svg-8489929 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-svg-8489929 .marker{fill:#666;stroke:#666;}#mermaid-svg-8489929 .marker.cross{stroke:#666;}#mermaid-svg-8489929 svg{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;}#mermaid-svg-8489929 p{margin:0;}#mermaid-svg-8489929 .label{font-family:"trebuchet ms",verdana,arial,sans-serif;color:#000000;}#mermaid-svg-8489929 .cluster-label text{fill:#333;}#mermaid-svg-8489929 .cluster-label span{color:#333;}#mermaid-svg-8489929 .cluster-label span p{background-color:transparent;}#mermaid-svg-8489929 .label text,#mermaid-svg-8489929 span{fill:#000000;color:#000000;}#mermaid-svg-8489929 .node rect,#mermaid-svg-8489929 .node circle,#mermaid-svg-8489929 .node ellipse,#mermaid-svg-8489929 .node polygon,#mermaid-svg-8489929 .node path{fill:#eee;stroke:#999;stroke-width:1px;}#mermaid-svg-8489929 .rough-node .label text,#mermaid-svg-8489929 .node .label text,#mermaid-svg-8489929 .image-shape .label,#mermaid-svg-8489929 .icon-shape .label{text-anchor:middle;}#mermaid-svg-8489929 .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#mermaid-svg-8489929 .rough-node .label,#mermaid-svg-8489929 .node .label,#mermaid-svg-8489929 .image-shape .label,#mermaid-svg-8489929 .icon-shape .label{text-align:center;}#mermaid-svg-8489929 .node.clickable{cursor:pointer;}#mermaid-svg-8489929 .root .anchor path{fill:#666!important;stroke-width:0;stroke:#666;}#mermaid-svg-8489929 .arrowheadPath{fill:#333333;}#mermaid-svg-8489929 .edgePath .path{stroke:#666;stroke-width:2.0px;}#mermaid-svg-8489929 .flowchart-link{stroke:#666;fill:none;}#mermaid-svg-8489929 .edgeLabel{background-color:white;text-align:center;}#mermaid-svg-8489929 .edgeLabel p{background-color:white;}#mermaid-svg-8489929 .edgeLabel rect{opacity:0.5;background-color:white;fill:white;}#mermaid-svg-8489929 .labelBkg{background-color:rgba(255, 255, 255, 0.5);}#mermaid-svg-8489929 .cluster rect{fill:hsl(0, 0%, 98.9215686275%);stroke:#707070;stroke-width:1px;}#mermaid-svg-8489929 .cluster text{fill:#333;}#mermaid-svg-8489929 .cluster span{color:#333;}#mermaid-svg-8489929 div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:12px;background:hsl(-160, 0%, 93.3333333333%);border:1px solid #707070;border-radius:2px;pointer-events:none;z-index:100;}#mermaid-svg-8489929 .flowchartTitleText{text-anchor:middle;font-size:18px;fill:#000000;}#mermaid-svg-8489929 rect.text{fill:none;stroke-width:0;}#mermaid-svg-8489929 .icon-shape,#mermaid-svg-8489929 .image-shape{background-color:white;text-align:center;}#mermaid-svg-8489929 .icon-shape p,#mermaid-svg-8489929 .image-shape p{background-color:white;padding:2px;}#mermaid-svg-8489929 .icon-shape rect,#mermaid-svg-8489929 .image-shape rect{opacity:0.5;background-color:white;fill:white;}#mermaid-svg-8489929 .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#mermaid-svg-8489929 .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#mermaid-svg-8489929 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}Routes toRoutes toRoutes toUser QuerySupervisor AgentReturns AgentWarranty AgentBilling AgentResponse

```
# Simplified LangGraph supervisor patternfrom langgraph.graph import StateGraph# Define specialized agentsreturns_agent = create_agent("You are an expert in returns...")warranty_agent = create_agent("You are an expert in warranties...")billing_agent = create_agent("You are an expert in billing...")# Supervisor routes to the right agentdef supervisor_node(state):    # LLM decides which agent should handle this    next_agent = supervisor_llm.invoke(state["messages"])    return {"next": next_agent}workflow = StateGraph()workflow.add_node("supervisor", supervisor_node)workflow.add_node("returns_agent", returns_agent)workflow.add_node("warranty_agent", warranty_agent)workflow.add_node("billing_agent", billing_agent)workflow.add_conditional_edges("supervisor", route_to_agent)
```


2. Multi-Agent Network


Agents communicate in a many-to-many pattern, where each agent can invoke others as needed. This provides flexibility but requires careful coordination logic.


#mermaid-svg-2998473{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;fill:#000000;}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#mermaid-svg-2998473 .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#mermaid-svg-2998473 .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#mermaid-svg-2998473 .error-icon{fill:#552222;}#mermaid-svg-2998473 .error-text{fill:#552222;stroke:#552222;}#mermaid-svg-2998473 .edge-thickness-normal{stroke-width:1px;}#mermaid-svg-2998473 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-svg-2998473 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-svg-2998473 .edge-thickness-invisible{stroke-width:0;fill:none;}#mermaid-svg-2998473 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-svg-2998473 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-svg-2998473 .marker{fill:#666;stroke:#666;}#mermaid-svg-2998473 .marker.cross{stroke:#666;}#mermaid-svg-2998473 svg{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;}#mermaid-svg-2998473 p{margin:0;}#mermaid-svg-2998473 .label{font-family:"trebuchet ms",verdana,arial,sans-serif;color:#000000;}#mermaid-svg-2998473 .cluster-label text{fill:#333;}#mermaid-svg-2998473 .cluster-label span{color:#333;}#mermaid-svg-2998473 .cluster-label span p{background-color:transparent;}#mermaid-svg-2998473 .label text,#mermaid-svg-2998473 span{fill:#000000;color:#000000;}#mermaid-svg-2998473 .node rect,#mermaid-svg-2998473 .node circle,#mermaid-svg-2998473 .node ellipse,#mermaid-svg-2998473 .node polygon,#mermaid-svg-2998473 .node path{fill:#eee;stroke:#999;stroke-width:1px;}#mermaid-svg-2998473 .rough-node .label text,#mermaid-svg-2998473 .node .label text,#mermaid-svg-2998473 .image-shape .label,#mermaid-svg-2998473 .icon-shape .label{text-anchor:middle;}#mermaid-svg-2998473 .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#mermaid-svg-2998473 .rough-node .label,#mermaid-svg-2998473 .node .label,#mermaid-svg-2998473 .image-shape .label,#mermaid-svg-2998473 .icon-shape .label{text-align:center;}#mermaid-svg-2998473 .node.clickable{cursor:pointer;}#mermaid-svg-2998473 .root .anchor path{fill:#666!important;stroke-width:0;stroke:#666;}#mermaid-svg-2998473 .arrowheadPath{fill:#333333;}#mermaid-svg-2998473 .edgePath .path{stroke:#666;stroke-width:2.0px;}#mermaid-svg-2998473 .flowchart-link{stroke:#666;fill:none;}#mermaid-svg-2998473 .edgeLabel{background-color:white;text-align:center;}#mermaid-svg-2998473 .edgeLabel p{background-color:white;}#mermaid-svg-2998473 .edgeLabel rect{opacity:0.5;background-color:white;fill:white;}#mermaid-svg-2998473 .labelBkg{background-color:rgba(255, 255, 255, 0.5);}#mermaid-svg-2998473 .cluster rect{fill:hsl(0, 0%, 98.9215686275%);stroke:#707070;stroke-width:1px;}#mermaid-svg-2998473 .cluster text{fill:#333;}#mermaid-svg-2998473 .cluster span{color:#333;}#mermaid-svg-2998473 div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:12px;background:hsl(-160, 0%, 93.3333333333%);border:1px solid #707070;border-radius:2px;pointer-events:none;z-index:100;}#mermaid-svg-2998473 .flowchartTitleText{text-anchor:middle;font-size:18px;fill:#000000;}#mermaid-svg-2998473 rect.text{fill:none;stroke-width:0;}#mermaid-svg-2998473 .icon-shape,#mermaid-svg-2998473 .image-shape{background-color:white;text-align:center;}#mermaid-svg-2998473 .icon-shape p,#mermaid-svg-2998473 .image-shape p{background-color:white;padding:2px;}#mermaid-svg-2998473 .icon-shape rect,#mermaid-svg-2998473 .image-shape rect{opacity:0.5;background-color:white;fill:white;}#mermaid-svg-2998473 .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#mermaid-svg-2998473 .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#mermaid-svg-2998473 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}User QueryAgent AAgent BAgent CAgent DResponse

```
# Multi-agent network patternfrom langgraph.graph import StateGraph# Each agent can invoke othersdef research_agent(state):    result = research_llm.invoke(state["messages"])    if needs_writing_help(result):        # Agent decides to call writing agent        return {"next": "writing_agent", "data": result}    return {"messages": result}def writing_agent(state):    result = writing_llm.invoke(state["messages"])    if needs_fact_check(result):        # Agent decides to call research agent        return {"next": "research_agent", "data": result}    return {"messages": result}# Build network with many-to-many connectionsworkflow = StateGraph()workflow.add_node("research_agent", research_agent)workflow.add_node("writing_agent", writing_agent)workflow.add_node("editing_agent", editing_agent)workflow.add_node("review_agent", review_agent)# Each agent can transition to multiple othersworkflow.add_conditional_edges("research_agent", route_from_research)workflow.add_conditional_edges("writing_agent", route_from_writing)workflow.add_conditional_edges("editing_agent", route_from_editing)
```


3. Hierarchical Teams


Supervisor agents manage their own teams of specialized agents, creating nested structures for complex workflows.


#mermaid-svg-4542973{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;fill:#000000;}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#mermaid-svg-4542973 .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#mermaid-svg-4542973 .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#mermaid-svg-4542973 .error-icon{fill:#552222;}#mermaid-svg-4542973 .error-text{fill:#552222;stroke:#552222;}#mermaid-svg-4542973 .edge-thickness-normal{stroke-width:1px;}#mermaid-svg-4542973 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-svg-4542973 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-svg-4542973 .edge-thickness-invisible{stroke-width:0;fill:none;}#mermaid-svg-4542973 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-svg-4542973 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-svg-4542973 .marker{fill:#666;stroke:#666;}#mermaid-svg-4542973 .marker.cross{stroke:#666;}#mermaid-svg-4542973 svg{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;}#mermaid-svg-4542973 p{margin:0;}#mermaid-svg-4542973 .label{font-family:"trebuchet ms",verdana,arial,sans-serif;color:#000000;}#mermaid-svg-4542973 .cluster-label text{fill:#333;}#mermaid-svg-4542973 .cluster-label span{color:#333;}#mermaid-svg-4542973 .cluster-label span p{background-color:transparent;}#mermaid-svg-4542973 .label text,#mermaid-svg-4542973 span{fill:#000000;color:#000000;}#mermaid-svg-4542973 .node rect,#mermaid-svg-4542973 .node circle,#mermaid-svg-4542973 .node ellipse,#mermaid-svg-4542973 .node polygon,#mermaid-svg-4542973 .node path{fill:#eee;stroke:#999;stroke-width:1px;}#mermaid-svg-4542973 .rough-node .label text,#mermaid-svg-4542973 .node .label text,#mermaid-svg-4542973 .image-shape .label,#mermaid-svg-4542973 .icon-shape .label{text-anchor:middle;}#mermaid-svg-4542973 .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#mermaid-svg-4542973 .rough-node .label,#mermaid-svg-4542973 .node .label,#mermaid-svg-4542973 .image-shape .label,#mermaid-svg-4542973 .icon-shape .label{text-align:center;}#mermaid-svg-4542973 .node.clickable{cursor:pointer;}#mermaid-svg-4542973 .root .anchor path{fill:#666!important;stroke-width:0;stroke:#666;}#mermaid-svg-4542973 .arrowheadPath{fill:#333333;}#mermaid-svg-4542973 .edgePath .path{stroke:#666;stroke-width:2.0px;}#mermaid-svg-4542973 .flowchart-link{stroke:#666;fill:none;}#mermaid-svg-4542973 .edgeLabel{background-color:white;text-align:center;}#mermaid-svg-4542973 .edgeLabel p{background-color:white;}#mermaid-svg-4542973 .edgeLabel rect{opacity:0.5;background-color:white;fill:white;}#mermaid-svg-4542973 .labelBkg{background-color:rgba(255, 255, 255, 0.5);}#mermaid-svg-4542973 .cluster rect{fill:hsl(0, 0%, 98.9215686275%);stroke:#707070;stroke-width:1px;}#mermaid-svg-4542973 .cluster text{fill:#333;}#mermaid-svg-4542973 .cluster span{color:#333;}#mermaid-svg-4542973 div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:12px;background:hsl(-160, 0%, 93.3333333333%);border:1px solid #707070;border-radius:2px;pointer-events:none;z-index:100;}#mermaid-svg-4542973 .flowchartTitleText{text-anchor:middle;font-size:18px;fill:#000000;}#mermaid-svg-4542973 rect.text{fill:none;stroke-width:0;}#mermaid-svg-4542973 .icon-shape,#mermaid-svg-4542973 .image-shape{background-color:white;text-align:center;}#mermaid-svg-4542973 .icon-shape p,#mermaid-svg-4542973 .image-shape p{background-color:white;padding:2px;}#mermaid-svg-4542973 .icon-shape rect,#mermaid-svg-4542973 .image-shape rect{opacity:0.5;background-color:white;fill:white;}#mermaid-svg-4542973 .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#mermaid-svg-4542973 .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#mermaid-svg-4542973 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}User QueryTop-Level SupervisorCustomer Service SupervisorTechnical Support SupervisorReturns AgentBilling AgentOrders AgentDiagnostics AgentInstallation AgentAPI Support AgentResponse

```
# Hierarchical teams patternfrom langgraph.graph import StateGraph# Top-level supervisordef main_supervisor(state):    category = categorize_query(state["messages"])    if category == "customer_service":        return {"next": "customer_service_supervisor"}    elif category == "technical":        return {"next": "technical_supervisor"}# Mid-level supervisors manage specialized teamsdef customer_service_supervisor(state):    subcategory = categorize_cs_query(state["messages"])    return {"next": f"{subcategory}_agent"}def technical_supervisor(state):    subcategory = categorize_tech_query(state["messages"])    return {"next": f"{subcategory}_agent"}# Build hierarchical structureworkflow = StateGraph()workflow.add_node("MS", main_supervisor)workflow.add_node("CSS", customer_service_supervisor)workflow.add_node("TS", technical_supervisor)# Add specialized agents under each supervisorworkflow.add_node("RA", returns_agent)workflow.add_node("BA", billing_agent)workflow.add_node("DA", diagnostics_agent)workflow.add_node("ASA", api_support_agent)workflow.add_conditional_edges("MS", route_to_team)workflow.add_conditional_edges("CSS", route_to_cs_agent)workflow.add_conditional_edges("TS", route_to_tech_agent)
```



### What LangGraph Excels At​


LangGraph is indeed excellent for:


- Workflow automation and orchestration
- Task decomposition into specialized subtasks
- Non-conversational agent applications
- Scenarios requiring a stencil control flow


The framework gives you precise control over execution paths, which is exactly what you want for many agentic processes, specifically ETL type of workflows.


But here's where the challenges arise...


![LangGraph Supervisor Pattern](https://www.parlant.io/img/supervisor-pattern.png)



## The Problem with Router Patterns​


Here's where things get interesting for conversational AI. The router pattern (i.e., "supervisor"), where specialized nodes own specific tasks and topics, works beautifully for workflow orchestration but creates inherent challenges when users engage in natural, free-form dialogue.


Let me walk you through the problems that arise from this architecture.



### Isolated Specialization Is Inherently Broken​


Picture this. A customer sends a message:



> "Hey, I need to return this laptop. Also, what's your warranty on replacements?"


In a router system, that message gets routed to one specialized agent.


Let's say it lands on the Returns Agent. This agent has a system prompt optimized for returns. It knows the return policy inside and out. But what about warranties? That's the Warranty Agent's domain.


The Returns Agent is now faced with four practical "alternatives" for handling the warranty question, none of which are actually any good:


Option 1: Ignore the warranty question



> "Sure, I can help you with that return. What's your order number?"


↪ Poor UX. The customer explicitly asked about warranties and got no acknowledgment.


This is not how a good conversational framework should behave.


Option 2: Acknowledge the limitation



> "I can help with the return. Regarding the warranty on replacements, I'm not certain about those details."


↪ This is not only awkward, but, from the overall agent's perspective, is incorrect. The overall agent can handle warranty questions—it just routed to the wrong specialized node. This will frustrate both users and developers, and lead to a disjointed user experience.


This, too, is not how a good conversational framework should behave.


Option 3: Hallucinate an answer



> "Sure! Our return policy is 30 days, and all replacements come with a 5-year warranty."


↪ Dangerous and extremely common—as well as hard to prevent with LLMs. The Returns Agent isn't grounded in warranty information, but, being an LLM, will often attempt to fabricate an answer. That "5-year warranty" might be completely wrong.


This, too, is not how a good conversational framework should behave.


Option 4: Stack the topics



> "Let me help you with that return first, and then we'll get to your warranty question."


↪ This is actually (kind of?) reasonable. The agent acknowledges both questions and proposes handling them sequentially. Many LangGraph implementations do exactly this.


But even option 4 is not how a good conversational framework should behave. It still smells of a fundamental design flaw, because it often leads to poor user experience.


When your AI user experience is poor, many users mistrust in it when it comes to important matters, and consequently drop out of your AI agent and escalate to a familiar human agent experience. That's where you're leaving money and customer satisfaction on the table.


Let's see how this leads to friction.



#### The First Common Issue: Intertwined Topics​


Many natural conversations don't present as "two separate questions." The "topics" (from a backend classification perspective) are naturally intertwined throughout the interaction. Forcing an artificial separation feels robotic. Consider this:



> "I bought this laptop for my business but it's broken. Can I return it and get a tax invoice for the replacement?"


The return process and the business tax documentation question aren't separate topics the user is stacking. They're deeply connected:


- The tax invoice depends on whether a return is processed
- Business customers may have different return policies
- The replacement timing affects when documentation is issued


Forcing the agent to say "Let me handle your return first, then we'll discuss invoicing" creates unnecessary friction and invites avoidable questions and objections.


In natural conversation, you'd expect both aspects to be addressed together:



> "Absolutely, we can process that return. For your replacement, I'll ensure you receive a proper tax invoice. Let me pull up your account—is the business registered under the same email?"


This is what a well-designed conversational framework should deliver, and it's exactly one of the design goals Parlant was built to achieve.



#### The Second Common Issue: Recurring Topics​


Another pattern that emerges frequently in natural conversation: topics don't just appear once and disappear. Users jump between topics, then circle back. And once multiple topics have entered the conversation, they tend to remain relevant—at least to some degree—for the rest of the discussion.


Consider this conversation flow:



> Customer: "I'd like to return this laptop I bought last week."
Agent (Returns): "I can help with that. Can you provide your order number?"
Customer: "Yeah let me get it, one sec. By the way, do you have the new model in stock? The one with the better battery?"
Agent (Inventory): "Yes, we have the XPS 15 with extended battery in stock. Would you like me to reserve one for you?"
Customer: "Yes, perfect. So if I return this one and get that new model, will I need to pay the difference, or can I just exchange them?"


Now the conversation needs to reference both the return process AND the inventory/pricing information. The customer isn't asking two separate questions—they're asking about the relationship between the return and the new purchase.


In a router system, this message gets routed to one specialized agent. If it goes to the Returns Agent, it can handle the return part but isn't grounded in current inventory pricing. Or perhaps it routes to the Billing Agent, which can discuss pricing but isn't grounded in returns.


The challenge is that once both topics have been introduced, the rest of the conversation will, in high likelihood, need to reference both in some form or another.


The user isn't thinking "Now I'm in Returns mode" or "Now I'm in Inventory mode". They're thinking about their situation holistically, which spans both domains.


Every subsequent message will be handled by one specialized node that's ungrounded with respect to the other relevant topic. The conversation's integrity and coherence fragments precisely when it needs to be most cohesive.


A conversational AI framework that's understands natural conversations should support seamless context switching and multi-topic awareness, and it's exactly one of the design goals Parlant was deliberately designed to achieve.



### Articulating the Core Design Issue​


When you route to a specialized node for topic X, that node is inherently unspecialized for topic Y.


Real conversations don't respect domain boundaries. Users mix topics in single messages, jump between topics, and expect coherent responses that integrate multiple contexts. A router/specialized node architecture forces you to choose one domain's grounding at the expense of others



## How Parlant Approaches Free-Form Conversation​


We created Parlant from a clear vision of, and frustration from these age-old problems in mechanistic AI conversations.


We thus decided to take a fundamentally different approach optimized for natural dialogue: dynamic assembly of a comprehensive context instead of artificially segmented routing.



### Dynamic Guideline Matching​


Rather than routing messages to specialized nodes, Parlant evaluates ALL of your guidelines and other contextual information, and loads only the relevant ones for each conversation turn—i.e., for each user-observable LLM request.



```
# Parlant approach - no routing, just conditional guidelinesawait agent.create_guideline(    condition="The customer wants to return an item",    action="First acknowledge their concern, explain our 30-day return policy, "           "and ask for their order number")await agent.create_guideline(    condition="The customer asks about warranty on replacements",    action="Explain that all replacement items come with our standard warranty, "           "which covers manufacturing defects for 1 year from the replacement date")await agent.create_guideline(    condition="The customer needs a tax invoice for a business purchase",    action="Let them know we'll include a proper tax invoice with their order documentation")await agent.create_guideline(    condition="The customer asks about store hours",    action="Tell them we're open Monday-Friday 9-8, Saturday 10-6, and Sunday 12-5")
```


Notice what's different here: there's no routing decision. When the customer says, "I need to return this laptop for my business and get a tax invoice for the replacement," Parlant's guideline matcher evaluates all guidelines and determines that three are contextually relevant:


1. The return guideline (customer wants to return)
2. The tax invoice guideline (business purchase context)
3. The warranty guideline (mentioned replacement)


They get loaded into the LLM's context simultaneously. The agent composes a response that's dynamically grounded in all of them:



> "I'd be happy to help you with that return and ensure you get proper documentation. Let me pull up your order—could you provide the order number? Once I have that, I'll process your return and make sure your replacement comes with a tax invoice for your business records. Just to confirm, the business is registered under the same email as this order?"


So, instead of choosing between domains, the Parlant agent assembles all the relevant grounding context on-demand.



### Why This Works for Conversational Coherence​


More often than not, real-world customer conversations break your textbook vision of an architected dialogue.


Parlant's approach solves the problems we identified earlier:


No artificial separation: The agent can naturally address intertwined topics because it has access to all relevant guidelines simultaneously.


No crude serialization: When both topics have brief answers, the agent can address them together naturally.


No context fragmentation: There's no handoff between agents because there aren't separate agents. There's just one agent with dynamically and continuously assembled context.


Consistent grounding: The agent is grounded in all contextually relevant information, not just one domain's specialization. This is (one) big part of what makes Parlant so seamlessly effective at maintaining compliance and avoiding hallucinations in customer-facing scenarios.



### How Parlant Keeps Accuracy Scalable​


Of course, if you just load all relevant guidelines, the LLM's context gets bloated. This is the same as putting everything in one giant system prompt, which leads to the "curse of instructions"—too many simultaneous instructions degrade performance (not to mention you'll ironically end up paying more for this degraded performance, due to the higher token count).


This is where Parlant's architecture does most of its work. The framework uses surprisingly intricate and nuanced guideline matching to accurately determine relevance BEFORE loading context.


#mermaid-svg-1303544{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;fill:#000000;}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#mermaid-svg-1303544 .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#mermaid-svg-1303544 .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#mermaid-svg-1303544 .error-icon{fill:#552222;}#mermaid-svg-1303544 .error-text{fill:#552222;stroke:#552222;}#mermaid-svg-1303544 .edge-thickness-normal{stroke-width:1px;}#mermaid-svg-1303544 .edge-thickness-thick{stroke-width:3.5px;}#mermaid-svg-1303544 .edge-pattern-solid{stroke-dasharray:0;}#mermaid-svg-1303544 .edge-thickness-invisible{stroke-width:0;fill:none;}#mermaid-svg-1303544 .edge-pattern-dashed{stroke-dasharray:3;}#mermaid-svg-1303544 .edge-pattern-dotted{stroke-dasharray:2;}#mermaid-svg-1303544 .marker{fill:#666;stroke:#666;}#mermaid-svg-1303544 .marker.cross{stroke:#666;}#mermaid-svg-1303544 svg{font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:16px;}#mermaid-svg-1303544 p{margin:0;}#mermaid-svg-1303544 .label{font-family:"trebuchet ms",verdana,arial,sans-serif;color:#000000;}#mermaid-svg-1303544 .cluster-label text{fill:#333;}#mermaid-svg-1303544 .cluster-label span{color:#333;}#mermaid-svg-1303544 .cluster-label span p{background-color:transparent;}#mermaid-svg-1303544 .label text,#mermaid-svg-1303544 span{fill:#000000;color:#000000;}#mermaid-svg-1303544 .node rect,#mermaid-svg-1303544 .node circle,#mermaid-svg-1303544 .node ellipse,#mermaid-svg-1303544 .node polygon,#mermaid-svg-1303544 .node path{fill:#eee;stroke:#999;stroke-width:1px;}#mermaid-svg-1303544 .rough-node .label text,#mermaid-svg-1303544 .node .label text,#mermaid-svg-1303544 .image-shape .label,#mermaid-svg-1303544 .icon-shape .label{text-anchor:middle;}#mermaid-svg-1303544 .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#mermaid-svg-1303544 .rough-node .label,#mermaid-svg-1303544 .node .label,#mermaid-svg-1303544 .image-shape .label,#mermaid-svg-1303544 .icon-shape .label{text-align:center;}#mermaid-svg-1303544 .node.clickable{cursor:pointer;}#mermaid-svg-1303544 .root .anchor path{fill:#666!important;stroke-width:0;stroke:#666;}#mermaid-svg-1303544 .arrowheadPath{fill:#333333;}#mermaid-svg-1303544 .edgePath .path{stroke:#666;stroke-width:2.0px;}#mermaid-svg-1303544 .flowchart-link{stroke:#666;fill:none;}#mermaid-svg-1303544 .edgeLabel{background-color:white;text-align:center;}#mermaid-svg-1303544 .edgeLabel p{background-color:white;}#mermaid-svg-1303544 .edgeLabel rect{opacity:0.5;background-color:white;fill:white;}#mermaid-svg-1303544 .labelBkg{background-color:rgba(255, 255, 255, 0.5);}#mermaid-svg-1303544 .cluster rect{fill:hsl(0, 0%, 98.9215686275%);stroke:#707070;stroke-width:1px;}#mermaid-svg-1303544 .cluster text{fill:#333;}#mermaid-svg-1303544 .cluster span{color:#333;}#mermaid-svg-1303544 div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:"trebuchet ms",verdana,arial,sans-serif;font-size:12px;background:hsl(-160, 0%, 93.3333333333%);border:1px solid #707070;border-radius:2px;pointer-events:none;z-index:100;}#mermaid-svg-1303544 .flowchartTitleText{text-anchor:middle;font-size:18px;fill:#000000;}#mermaid-svg-1303544 rect.text{fill:none;stroke-width:0;}#mermaid-svg-1303544 .icon-shape,#mermaid-svg-1303544 .image-shape{background-color:white;text-align:center;}#mermaid-svg-1303544 .icon-shape p,#mermaid-svg-1303544 .image-shape p{background-color:white;padding:2px;}#mermaid-svg-1303544 .icon-shape rect,#mermaid-svg-1303544 .image-shape rect{opacity:0.5;background-color:white;fill:white;}#mermaid-svg-1303544 .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#mermaid-svg-1303544 .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#mermaid-svg-1303544 :root{--mermaid-font-family:"trebuchet ms",verdana,arial,sans-serif;}User MessageGuideline MatchingTool CallingGenerate Response

## When LangGraph Works Well for Conversational AI​


I want to be clear: LangGraph isn't wrong for all conversational AI. If you have the right use case for it, you can achieve better results with it than with Parlant.


LangGraph works well for conversational agents when:


The conversation is narrow in scope, and streamlined: You're interviewing users through a specific process like onboarding, data collection, or a structured troubleshooting flow, where they have to choose their responses from options presented to then, rather than responding freely.


Users follow a guided path: The interaction model strictly requires users to answer questions in a formal sequence rather than conversing freely.


Limited conversational freedom: Users aren't expected to interrupt with unexpected questions mid-flow, change topics independently, or reference multiple contexts simultaneously.


Clear state transitions: The conversation has well-defined stages where it makes sense to "route" to the next step.


Granted, these are legitimate use cases where LangGraph is likely to provide great results with far less compute overhead than Parlant invests in (an investment made to maximize accuracy and user experience in genuine conversational settings).


The key distinction is in the interaction model. If your users are expected to follow a strict script at all times, LangGraph's routing works great and is not likely to run into unwieldy design issues and operational faults.


If your users are conversing naturally and freely, that's where the challenges emerge. That's where Parlant's shines, as it was intricately designed for this use case.



## Using LangGraph and Parlant Together​


Here's something interesting: these frameworks aren't competitive—they're complementary.


LangGraph can work as a lower-level orchestration tool within Parlant. Let me show you a practical example:



```
# A Parlant tool that uses LangGraph internally for complex retrieval@p.toolasync def find_relevant_documentation(    context: p.ToolContext,    query: str) -> p.ToolResult:    # LangGraph orchestrates the multi-step retrieval workflow    result = await langgraph_workflow.invoke({        "query": query,        "customer": p.Customer.current,    })    return p.ToolResult(        data=result["synthesized_answer"],        canned_response_fields={            "documentation": result["source_links"],        },    )# The tool is used within a Parlant guidelineawait agent.create_guideline(    condition="The customer asks about a technical feature or API",    action="Look up the info and provide an explanation if possible",    tools=[find_relevant_documentation],)
```


In this pattern:


- Parlant handles and synthesizes the conversational flow, dynamic context management, and natural dialogue
- LangGraph handles the complex internal KB workflow (retrieval, re-ranking, synthesis)


This combines the strengths of both:


- Parlant ensures coherent, well-guided, natural conversation
- LangGraph provides powerful workflow orchestration for agentic processing



## The Architectural Difference​


At the highest level, here's the core distinction:


LangGraph: Explicit Graph-Based Control Flow


LangGraph represents your application as a graph with explicit nodes and edges. You define the routing logic, specify transitions, and control execution flow. This is excellent for:


- Workflow automation
- Task decomposition
- Multi-step processes with clear stages
- Scenarios requiring precise control over execution order


It's great for when you know what the expect from the input—which is simply not the case for raw conversational content.


Parlant: Dynamic Context Assembly


That's where Parlant helps you keep the contracts under control, and handle the messy conversational parts cleanly and effectively.


Parlant represents your application as a set of conditional guidelines and journeys within a natural conversation.


Instead of routing between specialized nodes, it dynamically assembles relevant context for each turn. This is excellent for:


- Free-form conversational AI
- Natural dialogue where users don't follow scripts
- Scenarios where topics interweave unpredictably
- Compliance-critical customer-facing applications


Both approaches are valid. The right choice depends on your interaction model.



## When to Use Which​


Here's a practical guide:


Use LangGraph when you need explicit orchestration and precise control over execution: workflow automation like multi-step tasks, data processing pipelines, and agent workflows where order matters; task decomposition that breaks complex problems into coordinated subtasks or multi-agent collaboration for non-conversational workloads; narrow, guided conversational flows such as structured onboarding, step-by-step data collection, or troubleshooting wizards.


Use Parlant when you’re building free‑form, customer‑facing agents where users converse naturally without following a script: support chatbots, sales and consultation assistants, or any scenario that demands comprehensive and consistent domain alignment. It shines when conversations mix topics, include interruptions, and require natural back‑and‑forth; in compliance‑critical settings where regulated behavior and avoidance of unauthorized statements are essential across business‑critical interactions; and in multi‑context dialogues where users reference multiple topics simultaneously, concerns are intertwined rather than separable, and the agent must produce coherent, cross‑topic responses.


When you need both conversational fluidity and complex workflows, use both:


- Conversational agent (Parlant) with complex retrieval (LangGraph)
- Natural dialogue requiring multi-step tool orchestration
- Customer-facing AI with sophisticated backend processes



## "Can't I Just Build This with LangGraph?"​


At this point, you might be thinking: "Great, I understand the dynamic context assembly approach. Now why can't I just build that pattern myself using LangGraph?"


And the answer is: you absolutely can. LangGraph is flexible enough to implement a dynamic guideline matching and context assembly system like Parlant (though Parlant isn't actually built on top of it).


Nothing to stop you from building that. But, before you dive into it, consider that you'd be essentially building Parlant from scratch.


Why? Let me share a hard-earned lesson on how alignment engineering turned out to be a surprisingly deep rabbit hole.



### The Rabbit Hole Goes Deeper Than You Think​


When we started building Parlant, we thought dynamic context assembly would be straightforward. Match relevant guidelines, load them into context, done. We quickly learned that the complexity goes much deeper than initially apparent.


Guideline Matching Complexity:​
- Semantic matching isn't just about accuracy (though that alone is a massive challenge—just look at how many  specialized guideline sub-matchers exist in Parlant)
- You need to handle edge cases: partially relevant guidelines, conflicting conditions, different temporal scopes, and keeping track of what was already done and wasn't to avoid over-conformance to instructions
- False positives and negatives create different failure modes that need to be mitigated in how you think about your agent's design (which Parlant addresses through its conversation-optimized tool-calling and canned response systems)


Runtime Performance:​
Naive implementations create unacceptable latency; mitigating this requires well-tuned caching strategies and parallel execution of different pipeline stages—even at relatively small scale.


A Coherent, Holistic Architecture:​
Guidelines need to interact elegantly with tools. Journey state needs to be tracked; canned responses need to be coordinated with matched guidelines and tool outputs, and variables, glossaries, and relationships need to factor into context assembly.


Every component subtly influences the others in an integrated, closed loop that feels natural. Your development workflow all falls into place.


This is what Parlant offers, and it's truly taken a lot to get it here!



### Leverage Our Work & Research​


We've spent the last couple of years studying, building and refining these mechanisms—full time. Parlant's current implementation represents countless battle-tested iterations, performance optimizations, and lessons learned from real deployments. The guideline matching system alone has gone through multiple architectural rewrites as we tackled the surprising nuances of these challenges head-on.


If you're considering building your own dynamic context assembly system with LangGraph, I'd honestly encourage you to first:


1. Review Parlant's feature documentation to understand the full scope of challenges you'll encounter
2. Consider the engineering investment required to solve these problems elegantly
3. Evaluate whether your use case has unique requirements that Parlant doesn't address (for which a rewrite makes more sense than opening a Parlant GitHub issue or contributing a PR)



### Parlant is Fully Open Source​


Remember, Parlant isn't a black box. It's fully open source, which means you can:


- Inspect exactly how we solve these problems
- Extend or modify components to fit your needs
- Contribute improvements back to the community
- Build on top of years of production-hardened engineering by a decent team of developers!


Either way, understanding what's already been built and battle-tested can save you months of development time and help you avoid the pitfalls we've already encountered and solved—and will continue to solve and optimize for the emerging, modern Conversational AI community.



## Making the Right Choice​


The confusion between Parlant and LangGraph is understandable: They're both powerful frameworks for building with LLMs. But understanding the difference comes down to one key question:


What kind of interaction are you building?


If you're building workflows, orchestration, or guided processes → LangGraph is excellent.


If you're building free-form conversational AI where users don't follow a script → Parlant is designed specifically for this.


If you need both → They can work together beautifully.


It's clear that both frameworks have their place in the AI agent ecosystem. Choose based on your interaction model, and don't be afraid to use them together when it makes sense.


[Questions about Parlant?](https://discord.gg/duxWqxKk6J)

---


Have you tried building conversational agents with LangGraph or Parlant? I'd love to hear about your experience. Reach out on Discord or via our contact page.

Share post:[](https://www.linkedin.com/shareArticle?mini=true&url=https://www.parlant.io/blog/parlant-vs-langgraph/&text=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io)[](https://twitter.com/intent/tweet?url=https://www.parlant.io/blog/parlant-vs-langgraph/&text=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io)[](https://www.facebook.com/sharer/sharer.php?u=https://www.parlant.io/blog/parlant-vs-langgraph/)[](https://www.reddit.com/submit?url=https://www.parlant.io/blog/parlant-vs-langgraph/&title=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io)[](https://bsky.app/intent/compose?text=Found%20this%20really%20interesting%20blog%20post%20on%20Conversational%20AI%20by%20Parlant.io%20%20https%3A%2F%2Fwww.parlant.io%2Fblog%2Fparlant-vs-langgraph%2F)Tags:parlantai-agentslanggraphconversational-aimulti-agent-systems
