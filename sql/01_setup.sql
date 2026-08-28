-- ============================================================================
-- 01_setup.sql — run once, in the Snowsight worksheet, after your trial starts.
-- Creates a small warehouse, a scratch database for this demo's own tables,
-- and confirms you can see Snowflake's built-in sample e-commerce data
-- (TPC-H) without loading anything yourself.
-- ============================================================================

-- A tiny, cheap warehouse — this demo runs comfortably on an X-Small.
CREATE WAREHOUSE IF NOT EXISTS CKG_DEMO_WH
  WAREHOUSE_SIZE = 'XSMALL'
  AUTO_SUSPEND = 60          -- suspend after 60s idle; don't burn trial credits
  AUTO_RESUME = TRUE
  INITIALLY_SUSPENDED = TRUE;

USE WAREHOUSE CKG_DEMO_WH;

-- Scratch space for anything this demo writes (none of this touches the
-- read-only sample data share).
CREATE DATABASE IF NOT EXISTS CKG_DEMO;
CREATE SCHEMA IF NOT EXISTS CKG_DEMO.PUBLIC;
USE DATABASE CKG_DEMO;
USE SCHEMA PUBLIC;

-- Every Cortex AI Function call needs this. On a personal trial account
-- under ACCOUNTADMIN you already have it; this is here so the script is
-- correct for a shared/team account too.
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE ACCOUNTADMIN;

-- Confirm the sample e-commerce dataset is visible. TPC-H ships on every
-- Snowflake account as a read-only share — no ingestion, no CSV upload.
-- This demo uses ORDERS, LINEITEM, CUSTOMER, PART, SUPPLIER, NATION, REGION
-- from SNOWFLAKE_SAMPLE_DATA.TPCH_SF1 (the ~1GB scale factor — small enough
-- that every query here finishes in well under a second on an X-Small).
SELECT table_name, row_count
FROM SNOWFLAKE_SAMPLE_DATA.INFORMATION_SCHEMA.TABLES
WHERE table_schema = 'TPCH_SF1'
ORDER BY table_name;

-- Expect 8 rows: CUSTOMER, LINEITEM, NATION, ORDERS, PART, PARTSUPP,
-- REGION, SUPPLIER. If this returns nothing, the sample data share isn't
-- attached to your account (rare, but happens on some trial regions) —
-- see the README's "If the sample data isn't there" note.

-- Sanity-check a Cortex AI Function actually runs before we build anything
-- on top of it:
SELECT AI_COMPLETE('claude-sonnet-5', 'Reply with exactly: cortex is live') AS check;
