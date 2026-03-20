# Parlant Expert — Claude Code Plugin

A Claude Code plugin that makes Claude a proficient expert on the [Parlant](https://parlant.io) AI agent framework.

## What It Does

- Answers questions about Parlant concepts: guidelines, journeys, tools, variables, glossary, canned responses, retrievers, and more
- Guides you through building agents with the Parlant SDK
- Helps with production deployment, adapter selection, and architecture decisions
- Reads the full Parlant documentation on demand for detailed examples

## Loading the Plugin

### Local development (from the repo root)

```bash
claude --plugin-dir ./parlant-expert
```

### Via marketplace (from a fork)

```bash
# Add the marketplace
/plugin marketplace add owner/parlant-fork

# Install the plugin
/plugin install parlant-expert@parlant-fork
```

## Invocation

- **Automatic**: Ask any question about Parlant — the skill activates when it detects Parlant-related topics
- **Manual**: `/parlant-expert:parlant <your question>`

## Examples

```
How do I create a guideline in Parlant?
What's the difference between tools and retrievers?
Help me set up a journey with conditional transitions
/parlant-expert:parlant how does ARQ enforcement work?
```
