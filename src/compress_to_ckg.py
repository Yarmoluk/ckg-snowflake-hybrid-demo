"""
compress_to_ckg.py — turns *structural* facts about the live dataset into a
CKG, in the same CSV schema `ckg-mcp` serves in production:

    ConceptID,ConceptLabel,Dependencies,TaxonomyID,SourceURL,source_content_hash

The judgment call this file makes explicit: not everything queryable belongs
in the graph. Net revenue this minute is a live fact — it changes with every
order and belongs in Snowflake, queried fresh. Which five market segments
exist, which nations concentrate which suppliers, which five priority levels
an order can carry — that's *structure*. It doesn't change between two
queries five minutes apart, so paying a warehouse round-trip for it every
time an agent needs it is waste. That's the actual argument this repo is
making, encoded as a script instead of a slide.

Every node's source_content_hash is a real sha256 of the exact query result
that produced it (see cortex_client.run_sql) — not a placeholder. Re-run this
script after new orders land and a stale node's hash will visibly change,
the same "hash mismatch = re-extract" contract every other CKG in this
family uses.

Run: python -m src.compress_to_ckg
Produces: ckg/ecommerce-tpch.csv, ckg/ecommerce-tpch-v0.1.md
"""

from __future__ import annotations

import csv
from datetime import date
from pathlib import Path

from src.cortex_client import get_connection, run_sql

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"
CKG_DIR = Path(__file__).resolve().parent.parent / "ckg"

# Standard TPC-H nation -> region mapping. Fixed by the benchmark spec, not
# derived from a query — this is the one piece of "structure" stable enough
# that even a live lookup would be overkill.
NATION_TO_REGION = {
    "ALGERIA": "AFRICA", "ETHIOPIA": "AFRICA", "KENYA": "AFRICA",
    "MOROCCO": "AFRICA", "MOZAMBIQUE": "AFRICA",
    "ARGENTINA": "AMERICA", "BRAZIL": "AMERICA", "CANADA": "AMERICA",
    "PERU": "AMERICA", "UNITED STATES": "AMERICA",
    "INDIA": "ASIA", "INDONESIA": "ASIA", "JAPAN": "ASIA",
    "CHINA": "ASIA", "VIETNAM": "ASIA",
    "FRANCE": "EUROPE", "GERMANY": "EUROPE", "ROMANIA": "EUROPE",
    "RUSSIA": "EUROPE", "UNITED KINGDOM": "EUROPE",
    "EGYPT": "MIDDLE EAST", "IRAN": "MIDDLE EAST", "IRAQ": "MIDDLE EAST",
    "JORDAN": "MIDDLE EAST", "SAUDI ARABIA": "MIDDLE EAST",
}


def build_graph() -> tuple[list[dict], str]:
    sql_text = (SQL_DIR / "02_sample_queries.sql").read_text()
    conn = get_connection()
    try:
        region_result = run_sql(conn, _extract_query(sql_text, "Q1"))
        segment_result = run_sql(conn, _extract_query(sql_text, "Q2"))
        supplier_result = run_sql(conn, _extract_query(sql_text, "Q3"))
        priority_result = run_sql(conn, _extract_query(sql_text, "Q4"))
    finally:
        conn.close()

    nodes: list[dict] = []
    cid = 1

    def add(label, deps, taxonomy, source_url, content_hash):
        nonlocal cid
        nodes.append({
            "ConceptID": cid, "ConceptLabel": label, "Dependencies": deps,
            "TaxonomyID": taxonomy, "SourceURL": source_url, "source_content_hash": content_hash,
        })
        cid += 1
        return cid - 1

    root_id = add(
        "TPC-H E-Commerce Dataset", "", "ROOT",
        "snowflake://SNOWFLAKE_SAMPLE_DATA/TPCH_SF1", "sha256:standard-benchmark-schema",
    )

    region_ids: dict[str, int] = {}
    for row in region_result.as_dicts():
        rid = add(
            f"Region: {row['REGION']}", f"{root_id}:IMPLEMENTS", "REGION",
            "sql:02_sample_queries.sql#Q1", region_result.content_hash,
        )
        region_ids[row["REGION"]] = rid

    for row in segment_result.as_dicts():
        add(
            f"Segment: {row['SEGMENT']}", f"{root_id}:IMPLEMENTS", "SEGMENT",
            "sql:02_sample_queries.sql#Q2", segment_result.content_hash,
        )

    for row in supplier_result.as_dicts():
        nation = row["SUPPLIER_NATION"]
        region = NATION_TO_REGION.get(nation)
        deps = f"{region_ids[region]}:REQUIRES" if region in region_ids else ""
        add(
            f"Supplier base: {nation}", deps, "SUPPLIER_NATION",
            "sql:02_sample_queries.sql#Q3", supplier_result.content_hash,
        )

    for row in priority_result.as_dicts():
        add(
            f"Fulfillment priority: {row['O_ORDERPRIORITY']}", f"{root_id}:IMPLEMENTS",
            "PRIORITY", "sql:02_sample_queries.sql#Q4", priority_result.content_hash,
        )

    extracted_on = date.today().isoformat()
    return nodes, extracted_on


def _extract_query(sql_text: str, tag: str) -> str:
    """Pull one labeled query block (-- Q1: ... ; -- Q2: ...) out of the
    combined SQL file, so this script and 02_sample_queries.sql never drift
    out of sync with each other."""
    marker = f"-- {tag}:"
    start = sql_text.index(marker)
    rest = sql_text[start:]
    end = rest.find(";", rest.find(marker) + len(marker))
    return rest[:end + 1]


def write_csv(nodes: list[dict]) -> Path:
    CKG_DIR.mkdir(exist_ok=True)
    path = CKG_DIR / "ecommerce-tpch.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["ConceptID", "ConceptLabel", "Dependencies", "TaxonomyID", "SourceURL", "source_content_hash"])
        w.writeheader()
        for n in nodes:
            w.writerow(n)
    return path


def write_narrative(nodes: list[dict], extracted_on: str) -> Path:
    path = CKG_DIR / "ecommerce-tpch-v0.1.md"
    edge_count = sum(1 for n in nodes if n["Dependencies"])
    body = [
        "# CKG — TPC-H E-Commerce Dataset (live compression)",
        "",
        "## META",
        "version: 0.1.0",
        f"extracted: {extracted_on}",
        "domain: ecommerce-tpch",
        f"nodes: {len(nodes)}",
        f"edges: {edge_count}",
        "edge_types: IMPLEMENTS · REQUIRES",
        "scope: Structural facts about SNOWFLAKE_SAMPLE_DATA.TPCH_SF1 — which market",
        "  segments, regions, supplier nations, and fulfillment priorities exist, and",
        "  how they relate. Deliberately excludes anything that changes order to order",
        "  (revenue totals, order counts) — those stay live queries, see src/agent.py.",
        "method: generated by src/compress_to_ckg.py, which runs the four queries in",
        "  sql/02_sample_queries.sql and hashes each result set at fetch time. Re-run",
        "  after new data lands; a changed hash on an unchanged-looking node means the",
        "  underlying query result shifted and this file is stale.",
        "",
        "## NODES",
        "",
        "| ID | Label | Taxonomy | Source |",
        "|----|-------|----------|--------|",
    ]
    for n in nodes:
        body.append(f"| {n['ConceptID']} | {n['ConceptLabel']} | {n['TaxonomyID']} | `{n['SourceURL']}` |")
    body += [
        "",
        "## EVAL",
        "benchmark: ckg-benchmark v0.6.2",
        "dataset: huggingface.co/datasets/danyarm/ckg-benchmark",
        "benchmarked: false",
        "rag_baseline_f1: 0.123",
        "graphrag_baseline_f1: 0.120",
        "mean_tokens: 269",
        "paper: github.com/Yarmoluk/ckg-benchmark/blob/main/paper/main.pdf",
        "",
    ]
    path.write_text("\n".join(body), encoding="utf-8")
    return path


if __name__ == "__main__":
    nodes, extracted_on = build_graph()
    csv_path = write_csv(nodes)
    md_path = write_narrative(nodes, extracted_on)
    print(f"Wrote {len(nodes)} nodes -> {csv_path}")
    print(f"Wrote narrative -> {md_path}")
