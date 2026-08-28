-- ============================================================================
-- 02_sample_queries.sql — the "live" analytical queries this demo reasons
-- over. Standard TPC-H schema (SNOWFLAKE_SAMPLE_DATA.TPCH_SF1), read here as
-- an e-commerce dataset: CUSTOMER places ORDERS, each ORDER has LINEITEM rows
-- (the actual line-item purchases), each line item references a PART sourced
-- from a SUPPLIER, and both CUSTOMER and SUPPLIER sit in a NATION -> REGION
-- hierarchy. These are the queries src/agent.py calls for "live" facts, and
-- src/compress_to_ckg.py calls to derive the graph.
-- ============================================================================

USE DATABASE CKG_DEMO;
USE SCHEMA PUBLIC;
USE WAREHOUSE CKG_DEMO_WH;

-- Q1: Revenue by region — the top-level rollup a live dashboard needs fresh,
-- every time. This is exactly the kind of fact that should NEVER be baked
-- into a static graph, because it changes with every new order.
SELECT
    r.r_name                                        AS region,
    COUNT(DISTINCT o.o_orderkey)                     AS order_count,
    SUM(l.l_extendedprice * (1 - l.l_discount))      AS net_revenue
FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.REGION r
JOIN SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.NATION n   ON n.n_regionkey = r.r_regionkey
JOIN SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER c ON c.c_nationkey = n.n_nationkey
JOIN SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS o    ON o.o_custkey = c.c_custkey
JOIN SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.LINEITEM l  ON l.l_orderkey = o.o_orderkey
GROUP BY r.r_name
ORDER BY net_revenue DESC;

-- Q2: Revenue by customer market segment — five fixed values in this
-- dataset (AUTOMOBILE, BUILDING, FURNITURE, MACHINERY, HOUSEHOLD). The
-- *segment names and what they mean* are structural — they don't change
-- day to day, which is exactly why they belong in the compressed graph
-- rather than being re-queried every time an agent needs to know they exist.
SELECT
    c.c_mktsegment                                   AS segment,
    COUNT(DISTINCT c.c_custkey)                       AS customers,
    SUM(l.l_extendedprice * (1 - l.l_discount))       AS net_revenue,
    AVG(l.l_discount)                                 AS avg_discount
FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.CUSTOMER c
JOIN SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS o   ON o.o_custkey = c.c_custkey
JOIN SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.LINEITEM l ON l.l_orderkey = o.o_orderkey
GROUP BY c.c_mktsegment
ORDER BY net_revenue DESC;

-- Q3: Supplier concentration by nation — feeds the "structural" side of the
-- graph (which nations actually supply which part types), not a live number.
SELECT
    n.n_name                                         AS supplier_nation,
    COUNT(DISTINCT s.s_suppkey)                      AS supplier_count,
    COUNT(DISTINCT ps.ps_partkey)                    AS distinct_parts_supplied
FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.SUPPLIER s
JOIN SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.NATION n     ON n.n_nationkey = s.s_nationkey
JOIN SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.PARTSUPP ps  ON ps.ps_suppkey = s.s_suppkey
GROUP BY n.n_name
ORDER BY distinct_parts_supplied DESC;

-- Q4: Order fulfillment priority mix — a live operational number (today's
-- backlog shape), used in the demo to show the "must stay live" side of
-- the split.
SELECT
    o.o_orderpriority,
    COUNT(*) AS order_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct_of_orders
FROM SNOWFLAKE_SAMPLE_DATA.TPCH_SF1.ORDERS o
GROUP BY o.o_orderpriority
ORDER BY order_count DESC;
