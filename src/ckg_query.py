"""
ckg_query.py — the compressed-graph half of the hybrid.

Deliberately mirrors the tool semantics of `ckg-mcp` (list_domains,
search_concepts, query_ckg) at a scale that fits one file: load the CSV once,
answer structural questions from memory, no warehouse round-trip. This is
the "cheap and stays cheap" side of the split — see src/agent.py for where
this gets weighed against a live Snowflake call.
"""

from __future__ import annotations

import csv
from pathlib import Path

CKG_PATH = Path(__file__).resolve().parent.parent / "ckg" / "ecommerce-tpch.csv"


class CKG:
    def __init__(self, path: Path = CKG_PATH):
        if not path.exists():
            raise FileNotFoundError(
                f"{path} doesn't exist yet. Run `python -m src.compress_to_ckg` first "
                f"— it queries live Snowflake data and writes this file."
            )
        self.nodes: dict[str, dict] = {}
        with path.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                self.nodes[row["ConceptID"]] = row

    def search_concepts(self, query: str) -> list[dict]:
        """Case-insensitive substring match on the label — same contract as
        ckg-mcp's search_concepts: find the concept before you traverse it."""
        q = query.lower()
        return [n for n in self.nodes.values() if q in n["ConceptLabel"].lower()]

    def query_ckg(self, concept_id: str) -> dict:
        """Return one concept plus its direct dependencies (upstream) and
        anything that depends on it (downstream) — the same "local
        neighborhood" shape ckg-mcp's query_ckg returns, just without the
        multi-hop depth parameter (one file, no need for it)."""
        if concept_id not in self.nodes:
            raise KeyError(f"No concept {concept_id!r} in the graph")
        node = self.nodes[concept_id]
        upstream = self._parse_deps(node["Dependencies"])
        downstream = [
            {"id": n["ConceptID"], "label": n["ConceptLabel"]}
            for n in self.nodes.values()
            if concept_id in [d["target"] for d in self._parse_deps(n["Dependencies"])]
        ]
        return {
            "id": concept_id,
            "label": node["ConceptLabel"],
            "taxonomy": node["TaxonomyID"],
            "source": node["SourceURL"],
            "hash": node["source_content_hash"],
            "requires": upstream,
            "required_by": downstream,
        }

    @staticmethod
    def _parse_deps(raw: str) -> list[dict]:
        if not raw:
            return []
        out = []
        for part in raw.split("|"):
            target, _, edge_type = part.partition(":")
            out.append({"target": target, "type": edge_type or "RELATES_TO"})
        return out

    def as_context_block(self, max_nodes: int = 30) -> str:
        """A compact text rendering suitable for dropping straight into a
        prompt — this is the actual token-efficiency argument, made
        concrete: the whole structural graph, or a slice of it, in a few
        hundred tokens instead of re-deriving structure from a schema dump."""
        lines = []
        for n in list(self.nodes.values())[:max_nodes]:
            deps = ", ".join(d["target"] for d in self._parse_deps(n["Dependencies"])) or "—"
            lines.append(f"[{n['ConceptID']}] {n['ConceptLabel']} ({n['TaxonomyID']}) <- depends on: {deps}")
        return "\n".join(lines)
