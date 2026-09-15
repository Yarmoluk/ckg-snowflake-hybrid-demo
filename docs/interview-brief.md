# Interview brief

## 30-second walkthrough

> I built a small hybrid-agent pattern around Snowflake’s TPC-H sample data. The graph is generated from SQL result sets and stores typed structural facts—regions, customer segments, supplier structure, and fulfillment priorities—with a SHA-256 anchor for each result set. The agent has two separate tools: the graph for stable structure and Snowflake for live values. That avoids re-querying the warehouse for context while preserving the rule that current metrics are fetched live.

## Snowflake Semantic Views / Cortex Analyst

> I have implemented a native Semantic View artifact over the sample data, with logical tables, relationships, dimensions, metrics, synonyms, and Analyst guidance. I am careful about the scope: it is a self-directed, executable proof of concept and needs live validation in the target account. My prior semantic-layer work was the typed external CKG, which models business entities and the boundary between stable context and changing measures. The directly transferable work is modeling the business layer, validating joins and measures, and creating evaluation questions for Analyst.

## Cost-routing / MCP question

> I would not present this as a client MCP add-on or production deployment. It is a self-directed open-source proof of concept. The design makes the cost boundary explicit: a free in-memory CKG path for stable structural context and a paid live Snowflake path for current values. The visible orchestrator is direct Anthropic tool use; the repository also includes Snowflake Cortex `AI_COMPLETE` for in-account summarization.

## Technical tradeoff

> The important decision was what must remain live. Putting revenue and order counts into a graph would create a staleness problem, so I deliberately keep them in Snowflake. Structural concepts are compressed into the graph and retain query-result provenance. The agent uses both only when the question needs both.

## Enterprise next steps

1. Validate the Semantic View and create Cortex Analyst evaluation questions.
2. Add role-aware data access, certified query patterns, and business glossary ownership.
3. Make graph refresh incremental and attach freshness/policy metadata.
4. Instrument route quality, groundedness, latency, cost, and query failures.

## Do not claim

- Client delivery, production deployment, or a live Cortex Analyst implementation.
- That the CKG answers current revenue or order counts.
- That the direct-tool-use demo is an MCP service or a Snowflake Cortex Agent.
