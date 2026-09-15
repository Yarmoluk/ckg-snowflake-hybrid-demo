-- ============================================================================
-- 03_cortex_analyst_semantic_view.sql
--
-- A native Snowflake Semantic View for Cortex Analyst over TPC-H sample data.
-- It is intentionally small and auditable: three logical tables, two governed
-- joins, business dimensions, and defined metrics. It writes only the semantic
-- view into CKG_DEMO.PUBLIC; the base data remains Snowflake's read-only share.
--
-- Run after sql/01_setup.sql.
-- ============================================================================

USE WAREHOUSE CKG_DEMO_WH;
USE DATABASE CKG_DEMO;
USE SCHEMA PUBLIC;

CREATE OR REPLACE SEMANTIC VIEW TPCH_REVENUE_ANALYSIS
  TABLES (
    orders AS SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS
      PRIMARY KEY (o_orderkey)
      WITH SYNONYMS ('sales orders', 'purchases')
      COMMENT = 'Order-level business events',
    customers AS SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER
      PRIMARY KEY (c_custkey)
      WITH SYNONYMS ('buyers', 'accounts')
      COMMENT = 'Customer master data including market segment',
    line_items AS SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.LINEITEM
      PRIMARY KEY (l_orderkey, l_linenumber)
      WITH SYNONYMS ('order lines', 'purchases')
      COMMENT = 'Individual purchased items and discounts'
  )
  RELATIONSHIPS (
    orders_to_customers AS
      orders (o_custkey) REFERENCES customers,
    line_items_to_orders AS
      line_items (l_orderkey) REFERENCES orders
  )
  FACTS (
    line_items.line_item_id AS CONCAT(l_orderkey, '-', l_linenumber)
      COMMENT = 'Stable identifier for one order line',
    line_items.discounted_revenue AS l_extendedprice * (1 - l_discount)
      COMMENT = 'Extended line-item price after discount'
  )
  DIMENSIONS (
    customers.customer_name AS c_name
      WITH SYNONYMS ('customer name', 'buyer name')
      COMMENT = 'Customer name',
    customers.market_segment AS c_mktsegment
      WITH SYNONYMS ('segment', 'customer segment', 'market')
      COMMENT = 'TPC-H customer market segment',
    orders.order_date AS o_orderdate
      WITH SYNONYMS ('purchase date', 'order day')
      COMMENT = 'Date an order was placed',
    orders.order_year AS YEAR(o_orderdate)
      COMMENT = 'Calendar year an order was placed',
    orders.fulfillment_priority AS o_orderpriority
      WITH SYNONYMS ('priority', 'order priority')
      COMMENT = 'Order fulfillment priority'
  )
  METRICS (
    customers.customer_count AS COUNT(DISTINCT c_custkey)
      COMMENT = 'Number of customers',
    orders.order_count AS COUNT(DISTINCT o_orderkey)
      COMMENT = 'Number of orders',
    orders.average_order_value AS AVG(o_totalprice)
      WITH SYNONYMS ('average order value', 'aov')
      COMMENT = 'Average total price per order',
    line_items.net_revenue AS SUM(line_items.discounted_revenue)
      WITH SYNONYMS ('revenue', 'sales', 'net sales')
      COMMENT = 'Sum of extended price after line-item discount',
    line_items.line_item_count AS COUNT(line_items.line_item_id)
      COMMENT = 'Number of order line items'
  )
  COMMENT = 'Governed TPC-H revenue and orders semantic view for Cortex Analyst demo'
  AI_SQL_GENERATION 'Use net_revenue for revenue or sales questions. Use order_count for order-count questions. Do not infer a metric when the view does not define it.'
  AI_QUESTION_CATEGORIZATION 'Ask for clarification when a question does not specify whether it concerns orders, customers, or line items.';
