-- ============================================================================
-- 04_semantic_view_checks.sql — evidence that the native Semantic View exists
-- and that governed business definitions compile as Semantic SQL.
-- Run after sql/03_cortex_analyst_semantic_view.sql.
-- ============================================================================

USE WAREHOUSE CKG_DEMO_WH;
USE DATABASE CKG_DEMO;
USE SCHEMA PUBLIC;

SHOW SEMANTIC VIEWS LIKE 'TPCH_REVENUE_ANALYSIS';
DESCRIBE SEMANTIC VIEW TPCH_REVENUE_ANALYSIS;
SHOW SEMANTIC DIMENSIONS IN SEMANTIC VIEW TPCH_REVENUE_ANALYSIS;
SHOW SEMANTIC METRICS IN SEMANTIC VIEW TPCH_REVENUE_ANALYSIS;

-- Governed semantic SQL: revenue by a business dimension.
SELECT *
FROM SEMANTIC_VIEW(
  TPCH_REVENUE_ANALYSIS
  DIMENSIONS customers.market_segment
  METRICS line_items.net_revenue, orders.order_count
)
ORDER BY net_revenue DESC;

-- Governed semantic SQL: average order value by calendar year.
SELECT *
FROM SEMANTIC_VIEW(
  TPCH_REVENUE_ANALYSIS
  DIMENSIONS orders.order_year
  METRICS orders.average_order_value
)
ORDER BY order_year;
