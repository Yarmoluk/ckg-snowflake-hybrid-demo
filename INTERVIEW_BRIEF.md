# Interview brief — Snowflake × CKG hybrid demo

## 30-second walkthrough

“I built a small hybrid-agent pattern around Snowflake's TPC-H sample data. The graph is generated from four SQL result sets and stores typed structural facts—regions, customer segments, supplier bases, and fulfillment priorities—with a SHA-256 anchor for each result set. The agent has two deliberately separate tools: the graph for stable structure and Snowflake for live values. That lets it avoid re-querying the warehouse for context while preserving the rule that current metrics must be fetched live.”

Open the visual explorer first: `web/main.html` via a local HTTP server. Ask one structural question, one live-metric question, then the hybrid example. The key point is the decision boundary, not that every question is forced into a graph.

## Direct answers to the two recruiter questions

### 1. Have you built Snowflake semantic models / semantic views for Cortex Analyst?

“Not yet in the exact Cortex Analyst semantic-view format. My semantic-layer work here is a typed external CKG: it models stable business entities and relationships from Snowflake query results, preserves query provenance, and gives an agent a low-cost structural retrieval path. I would not represent that as Cortex Analyst delivery experience. The adjacent capability is real—modeling business concepts, separating dimensions from changing measures, and making the retrieval boundary explicit. My next implementation step would be to express the same TPC-H business model as Snowflake semantic views with logical tables, dimensions, measures, verified joins, and Analyst eval questions.”

### 2. Was the MCP add-on for Cortex costs client work, and did it reach production?

“I would not characterize this repository as a client MCP add-on or as production. It is a self-directed, open-source proof of concept. The code makes the cost boundary visible by separating a free in-memory CKG query from a paid live Snowflake query; the orchestrator chooses based on whether the question needs structural context, current values, or both. There is direct Snowflake Cortex `AI_COMPLETE` integration in the code for in-account summarization, while the two-tool orchestrator is built with direct Anthropic tool use. The repo documents its current verification scope, and I would describe it that way.”

## Strong follow-on answers

### What was technically difficult?

“The important design choice was deciding what must remain live. It is tempting to put everything into a graph. I intentionally kept revenue and order counts out because they can become stale; only structural facts are compressed. Each extracted structural node points back to the SQL query and the exact-result SHA-256 hash, so refresh and drift are explicit.”

### How would you make it enterprise-ready?

“I would start with the business glossary and Analyst semantic model: governed logical tables, dimensions, measures, relationships, certified query patterns, and role-based access. Then I would make graph refresh incremental, attach source and policy metadata, add route-quality and answer-groundedness evals, and instrument cost, latency, freshness, and query failures. The hard requirement is that the agent never uses cached structure to answer a question that needs a current regulated fact.”

### Why is this relevant to a healthcare or life-sciences role?

“The pattern is especially relevant where the source of truth is regulated and changes over time. It cleanly separates durable governed context—definitions, policy relationships, approved categories—from live operational facts. That improves explainability and provides a concrete place to attach provenance, access control, evaluation, and refresh policies.”

## Avoid saying

- “I shipped Cortex Analyst semantic views” — this repo does not demonstrate that.
- “This was a client implementation” or “production” — it is a self-directed proof of concept.
- “The graph answers live counts or revenue” — it deliberately does not.
- “MCP add-on” for this exact repo — the visible demo uses a direct tool-use agent, not an MCP server.
