"""
run_demo.py — the full walkthrough, start to finish.

    python -m demo.run_demo

Five steps, each printed as it happens so you can see where time and cost
actually go:

  1. Confirm the Snowflake connection and Cortex access work at all.
  2. Run the four live queries cold, and time them.
  3. Compress the structural results into a CKG (writes ckg/ecommerce-tpch.csv).
  4. Ask the hybrid agent two questions — one structural, one that needs a
     live number — and show which tool(s) it reaches for on each.
  5. Print a plain token/cost comparison: what it would have cost to answer
     the structural question by re-querying Snowflake every time, versus
     what the graph actually cost after the one-time compression.

This is meant to be read while it runs, not just executed.
"""

from __future__ import annotations

import time

from src.cortex_client import get_connection, run_sql, ask_claude_via_cortex
from src.compress_to_ckg import build_graph, write_csv, write_narrative
from src.ckg_query import CKG
from src.agent import ask as ask_agent


def step(n: int, title: str) -> None:
    print(f"\n{'=' * 70}\nSTEP {n} — {title}\n{'=' * 70}")


def main() -> None:
    step(1, "Connection + Cortex check")
    conn = get_connection()
    check = run_sql(conn, "SELECT AI_COMPLETE('claude-sonnet-5', 'reply with: ok') AS r")
    print(f"AI_COMPLETE round-trip: {check.rows[0][0]!r}")
    conn.close()

    step(2, "Live queries, timed")
    conn = get_connection()
    for tag in ["Q1", "Q2", "Q3", "Q4"]:
        from src.compress_to_ckg import _extract_query, SQL_DIR
        sql_text = (SQL_DIR / "02_sample_queries.sql").read_text()
        t0 = time.perf_counter()
        result = run_sql(conn, _extract_query(sql_text, tag))
        elapsed = time.perf_counter() - t0
        print(f"  {tag}: {len(result.rows)} rows in {elapsed:.2f}s — hash {result.content_hash[:19]}...")
    conn.close()

    step(3, "Compress structure into a CKG")
    nodes, extracted_on = build_graph()
    csv_path = write_csv(nodes)
    md_path = write_narrative(nodes, extracted_on)
    print(f"{len(nodes)} nodes written to {csv_path}")
    print(f"Narrative written to {md_path}")

    step(4, "Hybrid agent — structural question")
    print(ask_agent("What market segments exist in this dataset, and how many are there?"))

    step(5, "Hybrid agent — live-number question")
    print(ask_agent("What is the current net revenue for the AUTOMOBILE segment?"))

    step(6, "Cost shape, made concrete")
    ckg = CKG()
    context_block = ckg.as_context_block()
    print(
        "Asking 'what segments/regions/priorities exist' N times:\n"
        f"  live-query path   : N warehouse round-trips, ~{len(context_block.splitlines())} rows each time\n"
        f"  compressed-graph path: 1 compression (already paid for in step 3), then\n"
        f"                          {len(context_block)} chars (~{len(context_block)//4} tokens) reused every time\n"
        "The live path doesn't get cheaper by asking twice. The graph does."
    )


if __name__ == "__main__":
    main()
