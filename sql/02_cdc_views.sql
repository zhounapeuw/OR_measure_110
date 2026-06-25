-- ============================================================
-- 02_cdc_views.sql
-- CDC WONDER overdose deaths (6 drug files) + Oregon population.
-- ============================================================

-- Read all 6 monthly death files at once.
--  * ignore_errors=true  -> skip the notes/caveats footer rows at the bottom
--    of each file (they have the wrong number of columns).
--  * all_varchar=true    -> read everything as text first; "Deaths" mixes
--    numbers with the word "Suppressed", so we clean it ourselves below.
--  * filename=true       -> adds a column with the file path, so we can tell
--    which drug each row came from.
CREATE OR REPLACE VIEW raw_overdose AS
SELECT * FROM read_csv('cdc_wonder/OR overdose deaths*.csv',
    delim=',', header=true, all_varchar=true,
    ignore_errors=true, filename=true);

-- Tidy, one row per drug-month. Suppressed months are flagged, not dropped.
CREATE OR REPLACE VIEW stg_overdose_deaths AS
SELECT
    CASE                                            -- clean drug name from filename
        WHEN filename LIKE '%cocaine%'          THEN 'cocaine'
        WHEN filename LIKE '%psychostim_meth%'  THEN 'methamphetamine'
        WHEN filename LIKE '%heroin%'           THEN 'heroin'
        WHEN filename LIKE '%methadone%'        THEN 'methadone'
        WHEN filename LIKE '%other_opioids%'    THEN 'rx_opioids'
        WHEN filename LIKE '%other_synth_narc%' THEN 'synthetic_opioids_fentanyl'
    END                                            AS drug,
    CAST("Year Code" AS INT)                       AS year,
    CAST(split_part("Month Code", '/', 2) AS INT)  AS month,
    (Deaths = 'Suppressed')                        AS is_suppressed,
    TRY_CAST(Deaths AS INT)                        AS deaths_known  -- NULL if suppressed
FROM raw_overdose
WHERE "Month Code" SIMILAR TO '[0-9]{4}/[0-9]{2}';  -- keep real monthly rows only

-- Oregon population by year (tab-delimited file; same footer trick as above).
CREATE OR REPLACE VIEW stg_population AS
SELECT
    CAST(TRIM("Year Code") AS INT) AS year,
    CAST(Population AS BIGINT)      AS population
FROM read_csv('cdc_wonder/Multiple Cause of Death, 2018-2024, Single Race_population.xls',
    delim='\t', header=true, all_varchar=true, ignore_errors=true)
WHERE "Year Code" SIMILAR TO '[0-9]{4}';
