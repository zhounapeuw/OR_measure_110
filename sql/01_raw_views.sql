-- ============================================================
-- 01_raw_views.sql
-- "Raw" views: shortcuts that point at the source files in place.
-- Nothing is copied or imported; a view just reads the files when queried.
-- CREATE OR REPLACE means re-running this file is always safe.
-- ============================================================

-- Medicaid State Drug Utilization Data: all 8 yearly CSV files at once.
-- quote='"' tells the reader that some product names wrap commas in quotes
-- (e.g. "Creon 6,00"); union_by_name lines the files up by column name.
CREATE OR REPLACE VIEW raw_sdud AS
SELECT *
FROM read_csv_auto('sdud/*.csv', union_by_name=true, quote='"');
