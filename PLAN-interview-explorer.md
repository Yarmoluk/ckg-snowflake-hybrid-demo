# Snowflake CKG interview explorer plan

## Goal

Create a polished, locally runnable interactive view of the repository's existing
TPC-H CKG. It should make the hybrid design legible in an interview without
claiming Cortex Analyst, client delivery, production deployment, or results that
the repository does not support.

## Deliverables

1. A standalone interactive graph explorer under `web/` built from the checked-in
   `ckg/ecommerce-tpch.csv` artifact.
2. A compact interview brief with precise answers about semantic models, Cortex,
   provenance, query routing, and the honest scope of the demo.
3. A usage note in the repository README that makes the explorer easy to run.

## Implementation approach

- Render the 41-node graph with fixed, readable clusters and provenance details.
- Add a query line that classifies example questions as **CKG**, **live
  Snowflake**, or **both**. This is explicitly a transparent demo heuristic,
  not a live LLM or Snowflake execution surface.
- Provide node search, taxonomy filters, and source-hash details.
- Write interview language that converts the work into relevant capability while
  preserving the documented gaps: no Cortex Analyst semantic views, no client,
  and no production deployment claim.

## Validation

- Check graph-data counts and edge references against the CSV.
- Run a static local server, load the page, and inspect the browser output.
- Capture and visually review the final explorer before handoff.

## Status

- [x] Explorer, filters, provenance panel, and transparent query-routing demo implemented.
- [x] Interview brief written with explicit claim boundaries.
- [x] CSV integrity check completed: 41 nodes and 40 edges.
- [x] JavaScript syntax check completed.
- [ ] Browser screenshot/layout review requires a locally available Chrome runtime. The
  workspace's capture utility could not find a runnable Chrome binary, and the
  sandbox does not permit binding a local HTTP port.
- [x] Native semantic-view DDL and governed Semantic SQL verification script added.
- [ ] Live execution is blocked in this sandbox because Snowflake OAuth needs a local
  callback listener. Run the two SQL files in Snowsight or from Daniel's local terminal.

## Public documentation-site delivery

### Goal

Turn the repository into a credible public technical artifact: a concise README,
an MkDocs Material site, interactive demo entry points, and GitHub Pages
automation. The supplied Snowflake/Cortex artwork will identify the integration
theme without suggesting Snowflake endorsement or affiliation.

### Deliverables

1. A brand-forward MkDocs site covering the hybrid architecture, native Semantic
   View, live demos, reproducible setup, and claim-safe interview context.
2. A rewritten README that is useful to a recruiter, engineer, or evaluator in
   under two minutes, with direct links to the public site and runnable assets.
3. A GitHub Actions GitHub Pages workflow and docs-only dependency manifest.

### Validation

- Copy and inspect the provided SVG locally; retain it as a source asset inside
  the repository.
- Build the documentation with MkDocs in strict mode.
- Validate the checked-in graph data references before publishing.
- Push the completed public artifact and enable workflow-based GitHub Pages.
