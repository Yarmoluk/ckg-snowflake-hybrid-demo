# ckg-snowflake-hybrid-demo

![Hybrid context architecture: a knowledge graph and a Snowflake-style warehouse support a routed agent](assets/images/hybrid-context-architecture-hero.png)

A working demo of one idea: **an agent reasons better when it isn't forced to choose between a live database and a knowledge graph — it should have both, and know which one to reach for.**

Live Snowflake data answers "what's true right now" (revenue, order counts — anything that changes with the next order). A compressed knowledge graph answers "what exists and how does it relate" (segments, regions, supplier structure — facts stable enough that re-querying them every time is waste). This repo builds both, wires one Claude agent to both, and shows it picking the right one per question.

## Architecture

```
                    ┌─────────────────────────┐
                    │   Snowflake free trial   │
                    │  SNOWFLAKE_SAMPLE_DATA   │
                    │      .TPCH_SF1           │   e-commerce schema:
                    │  (orders/customers/      │   CUSTOMER -> ORDERS -> LINEITEM
                    │   parts/suppliers)       │   -> PART / SUPPLIER -> NATION -> REGION
                    └────────────┬─────────────┘
                                 │
                 ┌───────────────┴────────────────┐
                 │                                 │
        live SQL queries                  AI_COMPLETE('claude-sonnet-5', ...)
        (sql/02_sample_queries.sql)        = Claude, called *through* Cortex,
                 │                          reasoning next to the data
                 │                                 │
                 ▼                                 ▼
      src/compress_to_ckg.py            src/cortex_client.py
      hashes each result set,           .ask_claude_via_cortex()
      emits structural facts as
      a CKG (ckg/ecommerce-tpch.csv)
                 │
                 ▼
        src/ckg_query.py  ──────┐
        (free, in-memory)       │
                                 ▼
                        src/agent.py
                 one Claude agent (direct Anthropic API),
                 two tools: query_ckg (free) and
                 query_snowflake_live (costs a query) —
                 it decides which one a question needs
```

**Two different ways Claude shows up here, on purpose:**

| | Model access | What it's for |
|---|---|---|
| `AI_COMPLETE('claude-sonnet-5', ...)` inside SQL | Claude via **Snowflake Cortex** — no separate API key, billed to your Snowflake account, runs next to the data | Summarizing a query result without shipping rows out of the warehouse |
| The Anthropic API directly, with `tools=` | Claude via the **Anthropic API** — needs `ANTHROPIC_API_KEY` | The orchestrating agent, deciding whether a question needs the live path, the graph, or both |

That split is deliberate, not redundant: Cortex-native `AI_COMPLETE` is the right tool when reasoning should happen *inside* Snowflake's trust boundary; direct tool-use is the right tool when one agent needs to weigh two different systems against each other, which Cortex's own Agent framework can also do (see `snowflake-cortex-usage` note below) but this demo builds by hand so the decision logic is fully visible in one file.

## What "compressed into a knowledge graph format, like CKG" actually means here

`src/compress_to_ckg.py` doesn't summarize text — it runs four real SQL queries, and for anything **structural** (which segments exist, which nations supply which parts, which priority levels an order can carry), it writes a node into `ckg/ecommerce-tpch.csv` using the same schema `ckg-mcp` serves 328 production domains from:

```
ConceptID,ConceptLabel,Dependencies,TaxonomyID,SourceURL,source_content_hash
```

Every node's `source_content_hash` is a real `sha256` of the exact query result that produced it — not a placeholder, not a hash of a doc page (this isn't a web-scraped graph, so the provenance anchor here is a query result instead of a fetched URL, but the contract is identical: re-run the query, re-hash, and a mismatch means the underlying data moved). Anything that changes order-to-order — net revenue, order counts — is deliberately **left out** of the graph and stays a live query in `src/agent.py`. That line is the actual argument this repo makes.

## Setup

### 1. Snowflake free trial (~5 minutes, needs your email)

I can't do this step for you — it needs a real account:

1. Go to [signup.snowflake.com](https://signup.snowflake.com) and start a free trial (30 days, $400 credit as of 2026).
2. Pick **any cloud/region** — this demo doesn't care which. AWS is the default and fine.
3. Verify your email, set a password, log in to Snowsight.
4. In a new worksheet, run `sql/01_setup.sql` top to bottom. It creates a small warehouse, a scratch database, grants the Cortex role, confirms the sample e-commerce data is visible, and does a one-line `AI_COMPLETE` sanity check.
5. **If the sample data isn't there:** a small number of trial regions don't auto-attach `SNOWFLAKE_SAMPLE_DATA`. In Snowsight, go to **Data Products → Snowflake Data Marketplace**, search "Sample Data," and add it — it's free and instant.
6. **If `AI_COMPLETE` errors on `claude-sonnet-5`:** Cortex's available model list changes over time and varies by region — check **AI & ML → Studio** in Snowsight, or run `SHOW MODELS IN SNOWFLAKE.CORTEX;`, and swap the model name in `.env`/`src/cortex_client.py` if `claude-sonnet-5` isn't listed for your account yet.

### 2. Anthropic API key

Get one at [console.anthropic.com](https://console.anthropic.com) if you don't already have one — this powers `src/agent.py`, separate from the Cortex-native `AI_COMPLETE` calls.

### 3. Local environment

```bash
git clone https://github.com/Yarmoluk/ckg-snowflake-hybrid-demo.git
cd ckg-snowflake-hybrid-demo
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edit .env: your Snowflake account identifier, username, password, Anthropic key
```

Your Snowflake **account identifier** is the part of your Snowsight URL before `.snowflakecomputing.com` — e.g. if you log in at `https://ab12345.us-east-1.snowflakecomputing.com`, your `SNOWFLAKE_ACCOUNT` is `ab12345.us-east-1`.

## Running it

**Everything, in order, narrated:**
```bash
python -m demo.run_demo
```

**Or piece by piece:**
```bash
# Just compress the current live structure into a graph
python -m src.compress_to_ckg

# Ask the hybrid agent anything
python -m src.agent "Which region has the most orders, and what customer segments exist there?"
```

## Visual explorer

The checked-in graph also has a browser-based explainer: [`web/main.html`](web/main.html).
It renders the actual `ckg/ecommerce-tpch.csv` artifact as a queryable network and
shows the intended routing boundary between structural CKG retrieval and live
Snowflake SQL. It is deliberately a visual explainer, not a live-query console.

Run it from the repository root:

```bash
python3 -m http.server 8000
# then open http://localhost:8000/web/main.html
```

The graph, filters, provenance details, and query-router examples can be used as a
concise walkthrough in a technical interview. See [`INTERVIEW_BRIEF.md`](INTERVIEW_BRIEF.md)
for claim-safe talking points and exact answers about Cortex Analyst and production scope.

For a life-sciences-relevant companion demo, open
[`web/clinical-trials.html`](web/clinical-trials.html). It is a curated, public
ClinicalTrials.gov context graph of selected Otsuka-affiliated records—not a live
trial finder, medical advice, or a claim about the complete Otsuka portfolio.

## Native Cortex Analyst semantic view

`sql/03_cortex_analyst_semantic_view.sql` adds a native Snowflake Semantic View
over the same TPC-H sample data: logical tables, governed joins, dimensions,
facts, metrics, synonyms, and Cortex Analyst instructions. Run
`sql/04_semantic_view_checks.sql` immediately afterward to show the object,
inspect its dimensions/metrics, and execute two governed Semantic SQL queries.

This is deliberately separate from the CKG: the CKG remains the structural,
provenance-backed context layer; the Semantic View is the native governed layer
for Analyst-generated SQL.

That last question is a good one to try by hand — it needs **both** tools: "what segments exist" is structural (the graph answers it free), "most orders by region" is a current number (needs a live query). Watch which tools the agent reaches for and in what order.

## What I verified, and what I didn't

Everything here is written to run end-to-end against a real trial account. What I have **not** done: I don't have Snowflake credentials, so I have not executed this against a live account myself. The SQL is written against `SNOWFLAKE_SAMPLE_DATA.TPCH_SF1`'s standard, fixed schema (a public benchmark spec, not something that changes), and the Python has no logic that depends on guessed data shapes — but "the code is correct" and "I watched it run" are different claims, and I'm only making the first one. If you hit an error on first run, it's most likely one of the two "if" cases in Setup step 1 above (region-specific sample-data attachment, or a model name Cortex doesn't have live in your account yet) — both are environment differences I can't test for without an account.

## Why this matters for an FDE-shaped role

This is the same shape as a real forward-deployed problem: a customer has a live system of record (their warehouse) and an existing knowledge asset (docs, a wiki, a prior integration) — the wrong move is picking one and ignoring the other. The right move is exactly what `src/agent.py` does in miniature: give the agent both, make the tradeoff explicit in the tool descriptions, and let it reason over which one a given question actually needs.
