"""
cortex_client.py — the "live Snowflake" half of the hybrid.

Two things live here:
  1. A thin connection wrapper around snowflake-connector-python.
  2. `ask_claude_via_cortex()` — runs Claude *inside* Snowflake, via the
     AI_COMPLETE SQL function, so reasoning happens next to the data instead
     of round-tripping rows out to an external API call. This is what
     "Claude via the Cortex API" means in this demo: AI_COMPLETE's model
     argument is a Claude model (claude-sonnet-5 as of this writing — see
     README for how to check what your account currently has available),
     invoked through Snowflake's own Cortex entitlement, not a second
     Anthropic API key.

Separately, src/agent.py uses the *direct* Anthropic API (a real API key)
for the orchestrating agent that decides whether a question needs Snowflake,
the CKG, or both — see that file's docstring for why the split makes sense.
"""

from __future__ import annotations

import os
import hashlib
from dataclasses import dataclass

import snowflake.connector
from dotenv import load_dotenv

load_dotenv()


def get_connection() -> snowflake.connector.SnowflakeConnection:
    """One connection, built from .env. Raises loudly if a required var is missing
    rather than silently connecting with the wrong account."""
    required = ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD"]
    missing = [v for v in required if not os.environ.get(v)]
    if missing:
        raise RuntimeError(
            f"Missing required env vars: {', '.join(missing)}. "
            f"Copy .env.example to .env and fill them in from your trial account."
        )
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        password=os.environ["SNOWFLAKE_PASSWORD"],
        warehouse=os.environ.get("SNOWFLAKE_WAREHOUSE", "CKG_DEMO_WH"),
        database=os.environ.get("SNOWFLAKE_DATABASE", "CKG_DEMO"),
        schema=os.environ.get("SNOWFLAKE_SCHEMA", "PUBLIC"),
        role=os.environ.get("SNOWFLAKE_ROLE", "ACCOUNTADMIN"),
    )


@dataclass
class QueryResult:
    columns: list[str]
    rows: list[tuple]
    sql: str
    content_hash: str  # sha256 of the result set at fetch time — the provenance anchor

    def as_dicts(self) -> list[dict]:
        return [dict(zip(self.columns, row)) for row in self.rows]


def run_sql(conn: snowflake.connector.SnowflakeConnection, sql: str) -> QueryResult:
    """Run one statement, return columns + rows + a hash of the exact bytes
    fetched. This hash is what compress_to_ckg.py writes into each node's
    `source_content_hash` — the same trust-anchor pattern used everywhere else
    in the CKG standard, just anchored to a live query result instead of a
    fetched web page."""
    cur = conn.cursor()
    try:
        cur.execute(sql)
        columns = [c[0] for c in cur.description]
        rows = cur.fetchall()
    finally:
        cur.close()
    # Deterministic serialization before hashing — row order from Snowflake
    # is not guaranteed without ORDER BY, so hash what was actually returned,
    # not a re-sorted version of it. Callers that need reproducible hashes
    # should ORDER BY in the SQL itself (all queries in 02_sample_queries.sql
    # do).
    payload = "\n".join(",".join(str(v) for v in row) for row in rows).encode("utf-8")
    content_hash = "sha256:" + hashlib.sha256(payload).hexdigest()
    return QueryResult(columns=columns, rows=rows, sql=sql, content_hash=content_hash)


def ask_claude_via_cortex(
    conn: snowflake.connector.SnowflakeConnection,
    prompt: str,
    model: str = "claude-sonnet-5",
) -> str:
    """The "Claude via the Cortex API" call. AI_COMPLETE runs inside the
    warehouse, next to the data it's reasoning about — no data leaves the
    Snowflake account for this call. Escapes single quotes naively; fine for
    a demo, not a substitute for a bind variable in anything handling
    untrusted input."""
    escaped = prompt.replace("'", "''")
    result = run_sql(conn, f"SELECT AI_COMPLETE('{model}', '{escaped}') AS response")
    return result.rows[0][0]


def summarize_segment_via_cortex(
    conn: snowflake.connector.SnowflakeConnection,
    segment_name: str,
    stats_row: dict,
) -> str:
    """One concrete use of AI_COMPLETE: turn a row of aggregate numbers into
    a sentence a human or a downstream agent can use, without shipping the
    raw row out of Snowflake to do it."""
    prompt = (
        f"In one sentence, describe this e-commerce customer segment for a "
        f"business audience: segment={segment_name}, "
        f"customers={stats_row.get('CUSTOMERS')}, "
        f"net_revenue={stats_row.get('NET_REVENUE')}, "
        f"avg_discount={stats_row.get('AVG_DISCOUNT')}."
    )
    return ask_claude_via_cortex(conn, prompt)
