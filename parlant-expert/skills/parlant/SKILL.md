---
name: parlant
description: "Expert on the Parlant AI agent framework. Triggers when users ask about Parlant concepts (guidelines, journeys, tools, variables, glossary, canned responses, retrievers), Python SDK, TypeScript SDK (parlant-client), REST API endpoints, architecture, production deployment, adapters, or behavior modeling."
allowed-tools: Read, Glob, Grep, Agent
---

# Parlant Expert

You are an expert on the Parlant AI agent framework (https://parlant.io). You have deep knowledge of every concept, API, and pattern in Parlant. When answering questions, draw on the condensed knowledge below and use the `Read` tool to access full documentation files when detailed examples or precise code snippets are needed.

Parlant is a Python-based agent framework for building **compliant, controlled AI agents** for customer-facing use cases. Its core innovation is **Agentic Behavior Modeling (ABM)** — a paradigm where agent behavior is defined through structured behavioral primitives (guidelines, journeys, tools, variables, glossary, canned responses) rather than free-form prompts or rigid flow graphs.

Key value propositions:
- **Compliance**: ARQ (Attentive Reasoning Queries) enforcement ensures agents follow business rules
- **Control**: Behavior is modeled declaratively, not buried in prompts
- **Scalability**: Built for enterprise use with API hardening, auth, rate limiting, human handoff
- **Explainability**: Every agent decision can be traced and debugged via ARQ artifacts
- **Flexibility**: Guidelines activate dynamically based on conversation context, not rigid flows

---

## Core Concepts Quick Reference

### Agentic Behavior Modeling (ABM)

ABM sits between rigid flow engines (like IVR trees) and uncontrolled free-form prompting. Instead of scripting exact conversation paths or stuffing everything into a system prompt, you define **behavioral primitives** that the engine dynamically applies based on context. The engine uses LLM-based matching to decide which guidelines are relevant at each turn, then enforces them via ARQs.

### Key Entities

- **Server**: The runtime that hosts agents, manages stores, and serves the API. Created via `async with Server(...) as server`.
- **Agent**: A customized AI personality. Not a specialized function — one agent handles an entire domain. Behavior is shaped by attaching guidelines, journeys, tools, variables, glossary terms, and canned responses.
- **Customer**: Anyone interacting with the agent (end user, bot, human operator). Can be anonymous (guest) or registered with metadata and tags.
- **Session**: A continuous interaction between an agent and a customer. Event-driven and async — supports multiple messages before the agent responds.

### Guidelines

Guidelines are the core behavioral primitive — contextual condition/action pairs:
- **Condition**: When this guideline should activate (matched by the engine using LLM-based semantic matching)
- **Action**: What the agent should do when the condition is met

Key properties:
- **Dynamic matching**: The engine evaluates which guidelines match the current conversation context each turn
- **ARQ enforcement**: Each matched guideline generates an Attentive Reasoning Query that forces the LLM to explicitly reason about compliance
- **Tracking**: By default, guidelines are tracked (`track=True`) — once their action is fulfilled, they deactivate until the condition matches again. Set `track=False` for persistent guidelines.
- **Criticality**: `Criticality.LOW`, `MEDIUM`, `HIGH` — affects how much reasoning effort is spent on enforcement
- **Tool associations**: Guidelines can have tools attached that become available when the guideline activates
- **Canned responses**: Guidelines can restrict responses to pre-approved templates

Formulation best practices:
- Be **specific** and **bounded** — "If the customer asks about pricing, provide the current price list" not "Help with pricing"
- Conditions should be **observable** from conversation context
- Actions should be **concrete** and **verifiable**
- Avoid overlapping conditions unless you define relationships (priority, disambiguation)
- Use observational guidelines (condition only, no action) for context tracking

### Journeys

Journeys are state diagrams for multi-step conversational flows. They model processes like appointment scheduling, order tracking, or onboarding.

Components:
- **Title & Description**: What the journey is about
- **Conditions**: When to activate (list of condition strings or Guideline objects)
- **States**: Nodes in the state diagram
- **Transitions**: Edges between states (direct or conditional)

State types:
- `InitialJourneyState`: Auto-created entry point for every journey
- `ChatJourneyState`: Agent converses with the customer (created via `transition_to(chat_state="...")`)
- `ToolJourneyState`: Agent executes tools (created via `transition_to(tool_state=tool_entry)` or `transition_to(tool_instruction="...")`)
- `ForkJourneyState`: Splits into sub-paths (created via `.fork()`)
- `END_JOURNEY`: Special marker for journey termination

Transitions:
- **Direct**: `transition_to(chat_state="...")` — always taken when source state is active
- **Conditional**: `journey.create_transition(condition="...", source=state_a, target=state_b)` — taken when condition matches

Journey-scoped guidelines: You can create guidelines scoped to a journey (via `journey.create_guideline(...)`) that only activate when that journey is active.

### Tools

Tools are Python functions attached to guidelines that execute when the guideline activates. Defined with the `@tool` decorator:

```python
from parlant.sdk import tool, ToolContext, ToolResult

@tool
async def check_inventory(
    context: ToolContext,
    product_id: str,
) -> ToolResult:
    # ... lookup logic ...
    return ToolResult(data={"in_stock": True, "quantity": 42})
```

ToolResult properties:
- `data`: The main return value (any JSON-serializable data)
- `metadata`: Additional context for the engine (not shown to customer)
- `control`: Control flow signals (e.g., setting session to manual mode for human handoff)
- `canned_responses`: List of canned response templates to use for this response
- `canned_response_fields`: Field values for canned response template rendering

ToolParameterOptions: Fine-grained control over parameter behavior — enum values, choice providers, required/optional, Pydantic model support.

Tool reevaluation: Use `guideline.reevaluate_after(tool_entry)` to make the engine re-match guidelines after a tool executes (useful when tool results change context).

### Variables

Variables provide customer-specific or group-specific context to the agent:
- **Manual**: Set values directly via `variable.set_value_for_customer(customer, value)`
- **Tool-enabled**: Attach a tool that auto-fetches the value; use `freshness_rules` (cron expression) to control refresh frequency
- **Scopes**: Per-customer, per-tag (customer group), or global

### Glossary

Domain-specific terminology with name, description, and synonyms. Helps the agent understand domain jargon in both customer messages and guideline conditions. Created via `agent.create_term(name, description, synonyms=[...])`.

### Canned Responses

Pre-approved response templates that eliminate hallucinations for critical information:

Composition modes:
- `CompositionMode.FLUID`: Agent composes freely, using canned responses as reference material
- `CompositionMode.COMPOSITED`: Agent must compose from canned response fragments
- `CompositionMode.STRICT`: Agent must use canned responses verbatim (highest compliance)

Templates use Jinja2 syntax with field types:
- `std.*` fields: Standard fields (e.g., `std.customer_name`)
- Generative fields: LLM fills in dynamically
- Tool-based fields: Populated from `ToolResult.canned_response_fields`

Signals: Keywords that help the engine match the right canned response to the conversation context.

### Relationships

Define how guidelines and journeys interact:
- **Entailment**: `a.entail(b)` — when A matches, B is also included
- **Priority**: `a.prioritize_over(b)` — A takes precedence over B when both match
- **Dependency**: `a.depend_on(b)` — A only activates if B is also active
- **Disambiguation**: `a.disambiguate([b, c])` — engine asks for clarification when multiple match
- **Exclusion**: `a.exclude(b)` — Alias for `prioritize_over`; A takes precedence over B when both match

### Retrievers

RAG integration for grounding agent responses in external knowledge:
- **vs Tools**: Retrievers are for "knowing" (context), tools are for "doing" (actions)
- Define with `async def my_retriever(context: RetrieverContext) -> RetrieverResult`
- Attach to agents (`agent.attach_retriever(fn)`) or guidelines (`guideline.attach_retriever(fn)`)
- Session-scoped for context efficiency
- Can return `RetrieverResult(data=..., metadata=..., canned_responses=[...])` or `None`

### Sessions & Events

Sessions are event-driven and async:
- Event types: `message`, `status`, `tool`, `custom`
- Long-polling for real-time updates
- Supports multiple customer messages before agent responds
- Manual mode: Human operator takes over (for handoff scenarios)
- Labels: Categorize sessions for tracking/routing
- Metadata: Key-value pairs for custom session data

### Tags & Customer Groups

Tags group customers for shared behavior:
- Assign tags to customers, guidelines, variables, canned responses
- Variable values can be set per-tag (applying to all customers with that tag)
- Tag-based relationships for managing guideline groups

---

## SDK API Surface

### Server

```python
Server(
    host="0.0.0.0", port=8800, tool_service_port=8818,
    nlp_service=NLPServices.emcie,  # or .openai, .azure, .anthropic, .ollama, etc.
    session_store="transient" | "local" | str | SessionStore,
    customer_store="transient" | "local" | str | CustomerStore,
    variable_store="transient" | "local" | str | ContextVariableStore,
    log_level=LogLevel.INFO,
    modules=[],  # Plugin module paths
    migrate=False,
    configure_hooks=None,  # async (EngineHooks) -> EngineHooks
    configure_container=None,  # async (Container) -> Container
    initialize_container=None,  # async (Container) -> None
    configure_api=None,  # async (FastAPI) -> None
)
# Properties: .container, .logger, .ready, .api
# Use as: async with Server(...) as server:
```

### Agent

```python
agent = await server.create_agent(name, description, composition_mode=CompositionMode.FLUID,
    output_mode=OutputMode.BLOCK, max_engine_iterations=None, tags=[], id=None,
    perceived_performance_policy=None, preamble_config=None)

# Key methods:
await agent.create_guideline(condition, action, tools=[], criticality=Criticality.MEDIUM,
    canned_responses=[], composition_mode=None, matcher=None, track=True, labels=[], dependencies=[])
await agent.create_observation(condition, tools=[], criticality=Criticality.MEDIUM)  # No action
await agent.create_journey(title, description, conditions, composition_mode=None, labels=[], dependencies=[])
await agent.create_term(name, description, synonyms=[])
await agent.create_variable(name, description=None, tool=None, freshness_rules=None)
await agent.create_canned_response(template, tags=[], signals=[], metadata={}, field_dependencies=[])
await agent.attach_retriever(retriever_fn, id=None)
await agent.attach_journey(journey)
```

### Guideline

```python
# Relationships:
await guideline.entail(other_guideline)
await guideline.prioritize_over(other)
await guideline.exclude(other)
await guideline.depend_on(other)
await guideline.disambiguate([g1, g2])
await guideline.reevaluate_after(tool_entry)
await guideline.attach_retriever(retriever_fn, id=None)

# Constants:
Guideline.MATCH_ALWAYS  # Matcher that always returns matched=True
```

### Journey & States

```python
journey = await server.create_journey(title, description, conditions, tags=[], composition_mode=None)
# or
journey = await agent.create_journey(title, description, conditions)

# Build flow from initial state:
t1 = await journey.initial_state.transition_to(chat_state="How can I help?")
t2 = await t1.target.transition_to(tool_state=my_tool, condition="customer provides info")
t3 = await t2.target.transition_to(chat_state="Here are your results", condition="tool completed")
await t3.target.transition_to(state=END_JOURNEY)

# Fork:
fork_transition = await some_chat_state.fork()
await fork_transition.target.transition_to(chat_state="Path A", condition="...")
await fork_transition.target.transition_to(chat_state="Path B", condition="...")

# Journey-scoped guidelines:
await journey.create_guideline(condition="...", action="...")
await journey.depend_on(other_guideline_or_journey)
```

### Variable

```python
var = await agent.create_variable("plan_type", description="Customer's subscription plan",
    tool=plan_lookup_tool, freshness_rules="0 */6 * * *")  # Refresh every 6 hours

await var.set_value_for_customer(customer, "premium")
await var.set_value_for_tag(tag_id, "default_value")
await var.set_global_value("fallback")
value = await var.get_value_for_customer(customer)
```

### Customer & Session

```python
customer = await server.create_customer(name, metadata={}, tags=[], id=None)
# Customer.current — get current customer from context
# Customer.guest — anonymous customer

# Session is obtained via the API/client SDK, not created directly in the server SDK
# Session.current — get current session from context
```

### Auth & Rate Limiting

```python
from parlant.sdk import AuthorizationPolicy, BasicRateLimiter, ProductionAuthorizationPolicy

Server(
    configure_container=lambda c: c.register(AuthorizationPolicy, ProductionAuthorizationPolicy(...)),
)

# BasicRateLimiter(requests_per_minute=60)
```

### NLP Services

```python
from parlant.sdk import NLPServices

# Built-in providers:
NLPServices.emcie      # Default (Emcie inference platform)
NLPServices.openai     # OpenAI
NLPServices.azure      # Azure OpenAI
NLPServices.anthropic  # Anthropic Claude
NLPServices.ollama     # Local models via Ollama
NLPServices.vertex     # Google Vertex AI
NLPServices.gemini     # Google Gemini
NLPServices.cerebras   # Cerebras
NLPServices.together   # Together AI
NLPServices.litellm    # LiteLLM (universal adapter)
NLPServices.deepseek   # DeepSeek
NLPServices.mistral    # Mistral
NLPServices.qwen       # Qwen
# ... and more
```

### Key Enums & Types

```python
CompositionMode.FLUID | .COMPOSITED | .STRICT
OutputMode.BLOCK | .STREAM
Criticality.LOW | .MEDIUM | .HIGH
LogLevel.DEBUG | .INFO | .WARNING | .ERROR | .CRITICAL
EventKind  # message, status, tool, custom
EventSource  # customer, ai_agent, human_agent, system
```

---

## REST API Reference

The Parlant server exposes a REST API (FastAPI) at the configured host/port. Full API reference: https://www.parlant.io/docs/api/parlant-api/

### Health Check

```
GET /healthz → { "status": "ok" }
```

### Agents

```
POST   /agents                  → 201 AgentDTO
GET    /agents                  → 200 AgentDTO[]
GET    /agents/:agent_id        → 200 AgentDTO | 404
PATCH  /agents/:agent_id        → 200 AgentDTO | 404
DELETE /agents/:agent_id        → 204 | 404
```

**Create body**: `{ name, id?, description?, max_engine_iterations?, composition_mode?, message_output_mode?, tags? }`
**AgentDTO**: `{ id, name, description, creation_utc, max_engine_iterations, composition_mode, message_output_mode, tags }`

### Customers

```
POST   /customers               → 201 CustomerDTO
GET    /customers               → 200 CustomerDTO[]
GET    /customers/:customer_id  → 200 CustomerDTO | 404
PATCH  /customers/:customer_id  → 200 CustomerDTO | 404
DELETE /customers/:customer_id  → 204 | 404
```

**Create body**: `{ name, metadata?, tags? }`

### Sessions

```
POST   /sessions                → 201 SessionDTO
GET    /sessions                → 200 SessionDTO[] | SessionListingDTO
GET    /sessions/:session_id    → 200 SessionDTO | 404
PATCH  /sessions/:session_id    → 200 SessionDTO | 404
DELETE /sessions/:session_id    → 204 | 404
DELETE /sessions                → 204 (bulk delete)
```

**Create body**: `{ agent_id, customer_id?, title?, metadata?, labels? }`
**Query param** (create): `allow_greeting?: boolean`
**List query params**: `agent_id?, customer_id?, labels?, limit?, cursor?, sort? ("asc"|"desc")`
**SessionDTO**: `{ id, agent_id, customer_id, creation_utc, title, mode ("auto"|"manual"), consumption_offsets, metadata, labels }`

### Events (nested under sessions)

```
POST   /sessions/:session_id/events              → 201 EventDTO
GET    /sessions/:session_id/events              → 200 EventDTO[] | SSE stream
GET    /sessions/:session_id/events/:event_id    → 200 EventDTO
PATCH  /sessions/:session_id/events/:event_id    → 200 EventDTO
DELETE /sessions/:session_id/events              → 204 (by offset threshold)
```

**Create body**:
```json
{
  "kind": "message" | "tool" | "status" | "custom",
  "source": "customer" | "customer_ui" | "human_agent" | "human_agent_on_behalf_of_ai_agent" | "ai_agent" | "system",
  "message": "Hello...",           // Required for message events from customer/human_agent
  "data": {},                      // Required for custom events
  "metadata": {},                  // Optional key-value pairs
  "participant": { "id": "...", "display_name": "..." },  // For human_agent sources
  "status": "acknowledged" | "cancelled" | "processing" | "ready" | "typing" | "error",  // For status events
  "guidelines": [{ "action": "...", "rationale": "unspecified" | "buy_time" | "follow_up" }]  // For AI agent
}
```
**Query param** (create): `moderation?: "auto" | "paranoid" | "none"`

**EventDTO**:
```json
{
  "id": "evt_...",
  "source": "customer",
  "kind": "message",
  "offset": 0,
  "creation_utc": "2024-03-24T12:00:00Z",
  "trace_id": "corr_...",
  "correlation_id": "corr_...",
  "data": {
    "message": "The actual message text",
    "participant": { "id": "...", "display_name": "..." }
  },
  "metadata": {},
  "deleted": false
}
```

**Key**: The message text is in `data.message`, NOT at the top level.

**List events query params** (long-polling):
- `min_offset` — only events with offset >= this value
- `source` — filter by event source
- `trace_id` — filter by trace ID
- `kinds` — comma-separated string: `"message,status"`, `"message,tool"`
- `wait_for_data` — long-poll timeout in seconds (default 60; 0 = immediate return; >0 = wait for new events, 504 on timeout)
- `sse` — if `true`, returns `text/event-stream` (Server-Sent Events) instead of JSON array

### Terms (Glossary)

```
POST   /terms/:agent_id              → 201 TermDTO
GET    /terms/:agent_id              → 200 TermDTO[]
GET    /terms/:agent_id/:term_id     → 200 TermDTO | 404
PATCH  /terms/:agent_id/:term_id     → 200 TermDTO | 404
DELETE /terms/:agent_id/:term_id     → 204 | 404
```

**Create body**: `{ name, description, synonyms?, tags?, id? }`

### Guidelines

```
POST   /guidelines                   → 201 GuidelineDTO
GET    /guidelines                   → 200 GuidelineDTO[]
GET    /guidelines/:guideline_id     → 200 GuidelineDTO | 404
PATCH  /guidelines/:guideline_id     → 200 GuidelineDTO | 404
DELETE /guidelines/:guideline_id     → 204 | 404
```

### Canned Responses

```
POST   /canned_responses                          → 201 CannedResponseDTO
GET    /canned_responses                          → 200 CannedResponseDTO[]
GET    /canned_responses/:canned_response_id      → 200 CannedResponseDTO | 404
PATCH  /canned_responses/:canned_response_id      → 200 CannedResponseDTO | 404
DELETE /canned_responses/:canned_response_id      → 204 | 404
```

**Create body**: `{ value, fields?, tags?, signals?, metadata?, field_dependencies? }`

### Context Variables

```
POST   /context-variables                          → 201
GET    /context-variables                          → 200
GET    /context-variables/:variable_id             → 200 | 404
PATCH  /context-variables/:variable_id             → 200 | 404
DELETE /context-variables/:variable_id             → 204 | 404
GET    /context-variables/:variable_id/:key        → 200 (read value for customer/tag)
PUT    /context-variables/:variable_id/:key        → 200 (set value for customer/tag)
```

### Tags

```
POST   /tags              → 201
GET    /tags              → 200
GET    /tags/:tag_id      → 200 | 404
PATCH  /tags/:tag_id      → 200 | 404
DELETE /tags/:tag_id      → 204 | 404
```

### Services (Tool Services)

```
GET    /services          → 200 (list, no tool details)
GET    /services/:name    → 200 | 404 | 503 (full details with tools)
PUT    /services/:name    → 200 (create or update; name must be kebab-case)
DELETE /services/:name    → 204 | 404
```

### Journeys

```
POST   /journeys                         → 201
GET    /journeys                         → 200
GET    /journeys/:journey_id             → 200 | 404
PATCH  /journeys/:journey_id             → 200 | 404
DELETE /journeys/:journey_id             → 204 | 404
GET    /journeys/:journey_id/mermaid     → 200 text/plain (Mermaid stateDiagram)
```

### Other Endpoints

```
POST/GET/PATCH/DELETE  /relationships     — Guideline/tag relationships
POST/GET/PATCH/DELETE  /capabilities      — Capabilities (title, description, signals)
POST/GET               /evaluations       — Evaluation tasks
GET                    /logs              — WebSocket-based log streaming
```

### Server Lifecycle

The `async with Server()` pattern is a **setup-only block** — the HTTP server does NOT start inside the `async with` body. It starts in `__aexit__`:

```python
async with Server(
    host="0.0.0.0",
    port=8800,
    nlp_service=NLPServices.openai,
) as server:
    # Setup code runs here (create agents, guidelines, etc.)
    agent = await server.create_agent(name="My Agent")
    # ...
# HTTP server starts HERE (after exiting the block)
# Server runs until the process is terminated
```

The `server.ready` event is set when the health check (`/healthz`) succeeds. If you need to interact with the API programmatically after it starts, use `await server.ready.wait()` inside an `__aexit__`-triggered callback or a separate async task.

---

## TypeScript SDK (`parlant-client`)

The TypeScript SDK is an auto-generated REST client (via Fern) published on npm.

### Installation

```bash
npm install parlant-client
```

### Client Initialization

```typescript
import { ParlantClient } from 'parlant-client';

const client = new ParlantClient({
  environment: "http://localhost:8800"
});
```

### Key Methods

#### Sessions

```typescript
// Create a session
const session = await client.sessions.create({
  agentId: "ag_123",
  customerId: "cust_456",  // optional — guest if omitted
  title: "Support Chat",
  // metadata, labels also supported
});

// List sessions
const sessions = await client.sessions.list({
  agentId: "ag_123",
  labels: ["vip"],
});

// Read a session
const session = await client.sessions.read("session_id");
```

#### Events

```typescript
// Send a customer message
await client.sessions.createEvent("session_id", {
  kind: "message",
  source: "customer",
  message: "Hello, I need help"
});

// Long-poll for new events
const events = await client.sessions.listEvents("session_id", {
  minOffset: lastOffset,     // Only events after this offset
  waitForData: 30,           // Wait up to 30 seconds
  kinds: ["message", "status"]  // Filter by event kind
});

// Access message text from an event
const text = event.data.message;            // The message content
const sender = event.data.participant?.display_name;  // Sender name
const status = event.data.status;           // For status events
```

#### Agents

```typescript
// Create an agent
const agent = await client.agents.create({
  name: "Support Agent",
  description: "Handles customer inquiries"
});

// List agents
const agents = await client.agents.list();
```

### Complete Chat Integration Pattern

```typescript
import { ParlantClient } from 'parlant-client';

class ParlantChat {
  private client: ParlantClient;
  private sessionId: string | null = null;
  private lastOffset: number = 0;

  constructor(serverUrl: string) {
    this.client = new ParlantClient({ environment: serverUrl });
  }

  async createSession(agentId: string, customerId?: string): Promise<string> {
    const session = await this.client.sessions.create({
      agentId, customerId,
      title: `Chat ${new Date().toLocaleString()}`
    });
    this.sessionId = session.id;
    this.startEventMonitoring();
    return this.sessionId;
  }

  async sendMessage(message: string): Promise<void> {
    if (!this.sessionId) throw new Error('No active session');
    await this.client.sessions.createEvent(this.sessionId, {
      kind: "message",
      source: "customer",
      message
    });
  }

  private async startEventMonitoring(): Promise<void> {
    if (!this.sessionId) return;
    while (true) {
      try {
        const events = await this.client.sessions.listEvents(this.sessionId, {
          minOffset: this.lastOffset,
          waitForData: 30,
          kinds: ["message", "status"]
        });
        for (const event of events) {
          if (event.kind === "message") {
            console.log(`[${event.source}] ${event.data.message}`);
          } else if (event.kind === "status") {
            console.log(`Status: ${event.data.status}`);
          }
          this.lastOffset = Math.max(this.lastOffset, event.offset + 1);
        }
      } catch (error) {
        await new Promise(r => setTimeout(r, 5000));
      }
    }
  }
}
```

### React Widget (`parlant-chat-react`)

For quick React integration, use the official widget:

```bash
npm install parlant-chat-react
```

```jsx
import ParlantChatbox from 'parlant-chat-react';

<ParlantChatbox
  server="http://localhost:8800"
  agentId="your-agent-id"
  customerId="customer-123"     // optional
  sessionId="existing-session"  // optional, to resume
  float={true}                  // floating popup mode
/>
```

### SDK Field Name Mapping (REST vs TypeScript SDK)

The TypeScript SDK uses **camelCase** while the REST API uses **snake_case**:

| REST API field     | TypeScript SDK field |
|--------------------|---------------------|
| `agent_id`         | `agentId`           |
| `customer_id`      | `customerId`        |
| `session_id`       | `sessionId`         |
| `min_offset`       | `minOffset`         |
| `wait_for_data`    | `waitForData`       |
| `trace_id`         | `traceId`           |
| `display_name`     | `displayName`       |
| `creation_utc`     | `creationUtc`       |

---

## Architecture Guide

Parlant follows **Hexagonal Architecture** (Ports and Adapters):

- **`src/parlant/core/`**: Domain logic, interfaces (ports), engine pipeline. No external dependencies.
  - `engines/alpha/`: The main engine — guideline matching, ARQ generation, response composition
  - `services/tools/`: Tool plugin system, service registry
  - `nlp/`: NLP service interfaces (generation, embedding, moderation)
- **`src/parlant/adapters/`**: Implementations of core interfaces using third-party services (OpenAI, Azure, Ollama, Qdrant, Snowflake, etc.)
- **`src/parlant/api/`**: REST API layer using FastAPI. Consumes core modules.
- **`src/parlant/sdk.py`**: The public SDK — re-exports and wraps core types for ergonomic use.

**Engine pipeline** (per turn):
1. Collect context (session events, customer data, variables)
2. Match guidelines (LLM-based semantic matching against conversation context)
3. Resolve relationships (priority, entailment, dependency, disambiguation)
4. Execute tools (for matched guidelines with tool associations)
5. Generate ARQs (structured reasoning queries for each matched guideline)
6. Compose response (using ARQ results, canned responses, composition mode)

---

## Production Guidance

- **Input moderation**: Use `"auto"` mode (default) for content filtering, or `"paranoid"` for jailbreak protection. Supports OpenAI Omni Moderation and Lakera Guard.
- **Human handoff**: Set sessions to manual mode via tool control signals. Use event polling to bridge human operators. Parlant acts as single source of truth.
- **API hardening**: Use `ProductionAuthorizationPolicy` for JWT-based auth. Configure `BasicRateLimiter` for rate limiting. Use `configure_container` hook to register custom policies.
- **Custom frontends**: Use the official React widget (`parlant-chat-react`) for quick integration, or build custom UIs with the Python/TypeScript client SDKs.
- **Adapter selection**: Choose NLP providers based on requirements — `NLPServices.openai` for best quality, `.ollama` for local/private, `.azure` for enterprise compliance, `.vertex` for Google Cloud.
- **Agentic design**: Start simple, monitor, refine iteratively. Use canned responses for high-stakes content. Balance UX flexibility with business control.

---

## Documentation Index

When you need detailed examples, full API docs, or in-depth explanations, use the `Read` tool on these files. Paths are relative to the repository root.

### Quickstart
- `docs/quickstart/motivation.md` — ABM paradigm, why Parlant exists, comparison with other approaches
- `docs/quickstart/installation.md` — Installation, first agent setup, React widget, client SDKs
- `docs/quickstart/examples.md` — Healthcare agent example with journeys, tools, edge cases

### Core Concepts
- `docs/interactions.md` — Async interaction model, long-polling, event-driven architecture
- `docs/concepts/sessions.md` — Sessions, event types, storage options, client SDK usage
- `docs/concepts/entities/agents.md` — Agent identity, single vs multi-agent design
- `docs/concepts/entities/customers.md` — Customer types, tags, metadata, registration

### Customization
- `docs/concepts/customization/guidelines.md` — Guidelines deep dive, matching, ARQs, formulation best practices
- `docs/concepts/customization/journeys.md` — Journey states, transitions, scoped guidelines, context management
- `docs/concepts/customization/tools.md` — Tool decorator, ToolContext, ToolResult, parameter options, insights
- `docs/concepts/customization/canned-responses.md` — Templates, composition modes, signals, rendering pipeline
- `docs/concepts/customization/glossary.md` — Terms, descriptions, synonyms, when to use glossary vs guidelines
- `docs/concepts/customization/variables.md` — Manual vs tool-enabled, freshness rules, scoping
- `docs/concepts/customization/relationships.md` — Entailment, priority, dependency, disambiguation, exclusion
- `docs/concepts/customization/retrievers.md` — RAG integration, RetrieverContext, retriever vs tool distinction

### Production
- `docs/production/agentic-design.md` — Iterative development, compliance strategies, bounded flexibility
- `docs/production/api-hardening.md` — Authorization policies, rate limiting, JWT integration
- `docs/production/custom-frontend.md` — React widget, custom UI with client SDKs, event handling
- `docs/production/human-handoff.md` — Tier structure, manual mode, operator integration
- `docs/production/input-moderation.md` — Content filtering, auto/paranoid modes, provider integration

### Advanced
- `docs/advanced/contributing.md` — Contribution guidelines, DCO requirements
- `docs/advanced/custom-llms.md` — Custom NLP services, SchematicGenerator, Embedder, ModerationService, PromptBuilder
- `docs/advanced/engine-extensions.md` — Engine hooks, dependency injection, configure/initialize container
- `docs/advanced/explainability.md` — ARQ artifacts, debugging, guideline matching trace

### Adapters — NLP
- `docs/adapters/nlp/azure.md` — Azure OpenAI setup, auth methods, model configuration
- `docs/adapters/nlp/openrouter.md` — 400+ models, cost management, model selection guide
- `docs/adapters/nlp/snowflake-cortex.md` — Snowflake Cortex integration, data residency
- `docs/adapters/nlp/ollama.md` — Local LLMs, model recommendations, troubleshooting
- `docs/adapters/nlp/vertex.md` — Google Vertex AI, Claude and Gemini models

### Adapters — Persistence & Vector DB
- `docs/adapters/persistence/snowflake.md` — Snowflake persistence for sessions, customers, variables
- `docs/adapters/vector_db/qdrant.md` — Qdrant vector database setup, vector store types

### Blog Posts
- `docs/blog/parlant-3-3-release.md` — Tag-based relationships, numeric priorities, transient guidelines, Agent.utter()
- `docs/blog/parlant-3-2-streaming-responses.md` — Streaming, preamble config, labels, scoped retrievers
- `docs/blog/parlant-3-1-release.md` — Criticality, custom matchers, event handlers, linked journeys
- `docs/blog/parlant-3-0-release.md` — Parallel processing, canned responses, composition modes, API hardening
- `docs/blog/how-parlant-guarantees-compliance.md` — ARQ deep dive, compliance types, strict mode
- `docs/blog/inside-parlant-guideline-matching-engine.md` — Matching engine internals, optimization, evolution
- `docs/blog/criticality-in-customer-facing-agents.md` — Criticality levels, resource allocation
- `docs/blog/parlant-vs-dspy.md` — Parlant vs DSPy comparison, when to use each
- `docs/blog/parlant-vs-langgraph.md` — Parlant vs LangGraph comparison, combined usage
- `docs/blog/what-no-one-tells-you-about-agentic-api-design.md` — Tool/API design for LLMs, BFF pattern

---

## Common Task Patterns

### Writing Guidelines
1. Read `docs/concepts/customization/guidelines.md` for best practices
2. Keep conditions **observable** (based on what's in the conversation) and actions **concrete**
3. Use relationships to resolve conflicts between guidelines
4. Start with `Criticality.MEDIUM`, increase for compliance-critical rules
5. Anti-patterns: vague conditions ("customer needs help"), unbounded actions ("handle everything"), overlapping conditions without relationships

### Creating Tools
1. Use `@tool` decorator, accept `ToolContext` as first param, return `ToolResult`
2. Attach to guidelines — tools only execute when their guideline activates
3. Use `ToolParameterOptions` for enum values, choice providers, optional params
4. For side effects that change context, use `guideline.reevaluate_after(tool)` to re-trigger matching

### Setting Up Journeys
1. Design states as conversation phases, not individual messages
2. Use `ChatJourneyState` for conversation, `ToolJourneyState` for actions, `ForkJourneyState` for branching
3. Use conditional transitions for dynamic flow, direct transitions for linear steps
4. Scope guidelines to journeys for state-specific behavior
5. Use `END_JOURNEY` to terminate flows

### Deploying to Production
1. Choose appropriate NLP provider and configure auth
2. Set `session_store` and `customer_store` to persistent backends (not "transient")
3. Enable input moderation (auto or paranoid)
4. Configure `ProductionAuthorizationPolicy` and `BasicRateLimiter`
5. Use canned responses with `CompositionMode.STRICT` for compliance-critical content
6. Set up human handoff for edge cases

### Choosing Adapters
- Read the relevant adapter doc from `docs/adapters/` for setup instructions
- Consider: cost, latency, privacy/data residency, model quality, local vs cloud

### Troubleshooting with ARQ Explainability
1. Read `docs/advanced/explainability.md` for understanding ARQ artifacts
2. Check which guidelines matched and why via session events
3. Examine ARQ reasoning to understand why the agent behaved a certain way
4. Refine guideline conditions/actions based on matching results
