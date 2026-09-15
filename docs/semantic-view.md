# Native Cortex Analyst semantic view

`sql/03_cortex_analyst_semantic_view.sql` expresses the same business boundary in Snowflake-native form. It defines three logical tables—orders, customers, and line items—then adds governed relationships, business dimensions, metrics, synonyms, and generation guidance.

## What it models

| Semantic element | Included here |
| --- | --- |
| Logical tables | `orders`, `customers`, `line_items` |
| Governed joins | orders → customers; line items → orders |
| Dimensions | market segment, order date/year, fulfillment priority |
| Metrics | customer count, order count, average order value, net revenue, line-item count |
| Analyst guidance | metric selection and clarification rules |

## Run it in Snowsight

1. Run [`01_setup.sql`](https://github.com/Yarmoluk/ckg-snowflake-hybrid-demo/blob/main/sql/01_setup.sql).
2. Run [`03_cortex_analyst_semantic_view.sql`](https://github.com/Yarmoluk/ckg-snowflake-hybrid-demo/blob/main/sql/03_cortex_analyst_semantic_view.sql).
3. Run [`04_semantic_view_checks.sql`](https://github.com/Yarmoluk/ckg-snowflake-hybrid-demo/blob/main/sql/04_semantic_view_checks.sql) to inspect the object and exercise governed Semantic SQL queries.

```sql title="The core semantic boundary"
METRICS (
  orders.order_count AS COUNT(DISTINCT o_orderkey),
  line_items.net_revenue AS SUM(line_items.discounted_revenue)
    WITH SYNONYMS ('revenue', 'sales', 'net sales')
)
COMMENT = 'Governed TPC-H revenue and orders semantic view for Cortex Analyst demo'
AI_SQL_GENERATION 'Use net_revenue for revenue or sales questions. Use order_count for order-count questions.'
```

!!! warning "Claim boundary"
    The DDL is a native semantic-view implementation, but it has not been live-validated from this environment. Say it is *ready to run and validate in Snowflake*, not that it has already been deployed for a client or in production.

## Why both a Semantic View and a CKG?

They answer different needs. The Semantic View is Snowflake’s governed business layer for Analyst-generated SQL. The CKG is a compact, source-hashed retrieval layer for stable context that an agent can traverse without invoking a live warehouse query. The useful architecture is not a replacement story; it is a clear boundary between governed live metrics and reusable structural context.
