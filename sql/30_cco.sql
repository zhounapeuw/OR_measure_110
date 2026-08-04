-- ============================================================
-- 30_cco.sql
-- Create + load cco_metrics from the OHA "CCO Metrics: Overall Population" export.
-- One row per metric x CCO x measurement year (85 metrics, 16 CCOs + "CCO statewide",
-- 2011-2024). We slice to the SUD/IET measure in analysis queries.
--
-- Prereq: python loaders/load_cco.py   (writes staging/cco_metrics_overall.csv)
-- Run from project root:
--   psql -h 127.0.0.1 -U postgres -d measure110 -w -f sql/30_cco.sql
--
-- Key SUD/IET metric abbrevs:
--   IET_INI_18   = Initiation, ages 18+  (incentive; benchmark ~48.6%)
--   IET_ENG_18   = Engagement, ages 18+  (incentive; benchmark ~18.1%)
--   IET_INI_1317 / IET_ENG_1317 = ages 13-17 (not incentivized, no benchmark)
--   FUA7d / FUA30d = Follow-up after ED visit for SUD (7- and 30-day)
-- Note: denominators are only populated for the 'CCO statewide' row.
-- ============================================================

DROP TABLE IF EXISTS cco_metrics;
CREATE TABLE cco_metrics (
  year          int,
  rate_type     text,
  metric_abbrev text,
  metric_name   text,
  cco           text,
  service_rate  numeric,   -- proportion 0-1
  denominator   int,       -- statewide only
  benchmark     numeric    -- proportion 0-1 (NULL if not incentivized)
);
\copy cco_metrics FROM 'staging/cco_metrics_overall.csv' WITH (FORMAT csv, HEADER true)

-- County-level IET (18+) for the choropleth maps: one row per Oregon county,
-- initiation + engagement (proportions 0-1), latest measurement year. From the
-- Geographic Disparities workbook's per-county "CCO statewide" (= county total) row.
DROP TABLE IF EXISTS cco_county_iet;
CREATE TABLE cco_county_iet (
  county      text,
  state       text,
  initiation  numeric,
  engagement  numeric
);
\copy cco_county_iet FROM 'staging/cco_county_iet.csv' WITH (FORMAT csv, HEADER true)
