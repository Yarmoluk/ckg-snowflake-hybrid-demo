"""
agent.py — the part that actually demonstrates "unified reasoning."

One Claude agent (direct Anthropic API, tool use), two tools:

  query_ckg              — the compressed graph. Free after the initial
                            compression. Answers "what exists and how does
                            it relate" — segments, regions, supplier nations,
                            fulfillment priorities.
  query_snowflake_live    — a live warehouse query. Costs a query, every
                            time. Answers "what's true right now" — revenue,
                            order counts, anything that changes between two
                            questions asked five minutes apart.

Why two tools and not one: collapsing them into a single "ask about the
data" tool would hide the actual design decision this repo is arguing for —
that an agent should reach for the free, structural answer first and pay for
a live query only when the question actually requires current truth. Giving
Claude both tools, undifferentiated except by name and description, and
watching which one it reaches for on a given question, is the honest way to
show that the model itself makes the right call when the option exists —
not because it was scripted to, but because the tool descriptions state the
real tradeoff and it reasons over that.

Run: python -m src.agent "your question here"
"""

from __future__ import annotations

import json
import os
import sys

from anthropic import Anthropic
from dotenv import load_dotenv

from src.cortex_client import get_connection, run_sql
from src.ckg_query import CKG

load_dotenv()

TOOLS = [
    {
        "name": "query_ckg",
        "description": (
            "Search the compressed structural knowledge graph of this e-commerce "
            "dataset — which market segments, regions, supplier nations, and "
            "fulfillment priorities exist, and how they relate. Free — no warehouse "
            "query. Use this FIRST for any question about categories, relationships, "
            "or 'what kinds of X exist.' Do NOT use this for current numbers "
            "(revenue, counts, totals) — those aren't in the graph on purpose."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"concept": {"type": "string", "description": "Search term, e.g. 'AUTOMOBILE' or 'region'"}},
            "required": ["concept"],
        },
    },
    {
        "name": "query_snowflake_live",
        "description": (
            "Run a live SQL query against the Snowflake warehouse. Costs a real "
            "query. Use this ONLY when the question needs a current number — "
            "revenue, order counts, averages — that changes as new orders land "
            "and therefore can't live in a static graph."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"sql": {"type": "string", "description": "A SELECT statement against SNOWFLAKE_SAMPLE_DATA.TPCH_SF1 or CKG_DEMO tables"}},
            "required": ["sql"],
        },
    },
]

SYSTEM_PROMPT = (
    "You answer questions about an e-commerce dataset using two tools: a free "
    "compressed knowledge graph for structure (query_ckg) and a live Snowflake "
    "query for current numbers (query_snowflake_live). Prefer query_ckg whenever "
    "the question is about categories or relationships rather than a specific "
    "current figure. State which tool(s) you used and why in your final answer."
)


def run_tool(name: str, tool_input: dict, ckg: CKG, sf_conn) -> str:
    if name == "query_ckg":
        matches = ckg.search_concepts(tool_input["concept"])
        if not matches:
            return json.dumps({"matches": [], "note": "no structural concept matched — this may need a live query instead"})
        return json.dumps({"matches": [ckg.query_ckg(m["ConceptID"]) for m in matches[:5]]})
    if name == "query_snowflake_live":
        result = run_sql(sf_conn, tool_input["sql"])
        return json.dumps({"columns": result.columns, "rows": result.rows[:20]}, default=str)
    raise ValueError(f"Unknown tool: {name}")


def ask(question: str, max_turns: int = 4) -> str:
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    ckg = CKG()
    sf_conn = get_connection()

    messages = [{"role": "user", "content": question}]
    tool_log: list[str] = []

    try:
        for _ in range(max_turns):
            response = client.messages.create(
                model="claude-sonnet-5",
                max_tokens=1024,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages,
            )
            if response.stop_reason != "tool_use":
                final_text = "".join(b.text for b in response.content if b.type == "text")
                print("\n--- tools called, in order ---")
                print("\n".join(tool_log) or "(none — answered from the model directly)")
                return final_text

            messages.append({"role": "assistant", "content": response.content})
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                tool_log.append(f"{block.name}({json.dumps(block.input)})")
                output = run_tool(block.name, block.input, ckg, sf_conn)
                tool_results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
            messages.append({"role": "user", "content": tool_results})

        return "(hit max_turns without a final answer — inspect the transcript)"
    finally:
        sf_conn.close()


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or (
        "Which customer segment has the highest average discount, and what does "
        "that segment mean in this dataset?"
    )
    print(f"Q: {q}\n")
    print(ask(q))
