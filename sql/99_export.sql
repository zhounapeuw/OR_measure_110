-- ============================================================
-- 99_export.sql
-- Write the analysis-ready mart tables to CSV for Tableau.
-- Tableau connects to these small files (not the 4 GB of raw data).
-- The exports/ folder is created by build_db.py before this runs.
-- ============================================================

COPY mart_overdose_rate TO 'exports/overdose_rate.csv' (HEADER, DELIMITER ',');
