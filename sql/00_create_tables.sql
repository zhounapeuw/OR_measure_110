-- ============================================================
-- 00_create_tables.sql
-- Create and load the source tables from the staging CSVs.
--
-- Prereq: run the loaders first so the staging files exist:
--     python loaders/load_sdud.py
--     python loaders/load_cdc.py
--
-- Run this file from the project root so the \copy paths resolve:
--     psql -h 127.0.0.1 -U postgres -d measure110 -w -f sql/00_create_tables.sql
--
-- DROP TABLE IF EXISTS: each table is deleted first and then
-- rebuilt from the staging CSVs, so you always get a fresh copy - never
-- duplicate rows, and no error if the table doesn't exist yet.
-- (\copy is a psql client command, so this file is run with psql, not the server.)
-- ============================================================

-- --- Medicaid State Drug Utilization Data (Oregon only) ---
DROP TABLE IF EXISTS sdud_or;
CREATE TABLE sdud_or (
  utilization_type               text,
  state                          text,
  ndc                            text,
  labeler_code                   text,
  product_code                   text,
  package_size                   text,
  year                           int,
  quarter                        int,
  suppression_used               boolean,
  product_name                   text,
  units_reimbursed               numeric,
  number_of_prescriptions        numeric,
  total_amount_reimbursed        numeric,
  medicaid_amount_reimbursed     numeric,
  non_medicaid_amount_reimbursed numeric
);
\copy sdud_or FROM 'staging/sdud_or.csv' WITH (FORMAT csv, HEADER true)

-- --- CDC WONDER overdose deaths (one row per drug-month) ---
DROP TABLE IF EXISTS overdose_deaths;
CREATE TABLE overdose_deaths (
  drug          text,
  year          int,
  month         int,
  is_suppressed boolean,
  deaths_known  int
);
\copy overdose_deaths FROM 'staging/overdose_deaths.csv' WITH (FORMAT csv, HEADER true)

-- --- Oregon population by year ---
DROP TABLE IF EXISTS population;
CREATE TABLE population (
  year       int,
  population bigint
);
\copy population FROM 'staging/population.csv' WITH (FORMAT csv, HEADER true)
