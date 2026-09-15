# Run the demo

## Prerequisites

- A Snowflake account with access to `SNOWFLAKE_SAMPLE_DATA.TPCH_SF1`.
- A warehouse and credentials permitted to use the demo database.
- An Anthropic API key only if you want to run the direct-tool-use orchestrator.

## 1. Prepare Snowflake

In Snowsight, run the SQL files in this order:

```text
sql/01_setup.sql
sql/02_sample_queries.sql
sql/03_cortex_analyst_semantic_view.sql
sql/04_semantic_view_checks.sql
```

The setup script creates the small demo warehouse and `CKG_DEMO` database. The TPC-H base tables remain Snowflake sample data.

## 2. Run the Python agent

```bash
git clone https://github.com/Yarmoluk/ckg-snowflake-hybrid-demo.git
cd ckg-snowflake-hybrid-demo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Add Snowflake credentials and, for src.agent, ANTHROPIC_API_KEY.
python -m demo.run_demo
```

To regenerate the graph from your live structural extracts:

```bash
python -m src.compress_to_ckg
```

## 3. Run the visual explorer locally

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000/web/main.html`.

The browser explorer is intentionally a transparent client-side routing demonstration. It does not execute Snowflake SQL or call an LLM from the browser.

## Documentation development

```bash
pip install -r requirements-docs.txt
mkdocs serve
```

The production documentation build runs automatically through GitHub Pages on pushes to `main`.
