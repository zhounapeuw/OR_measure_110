-- ============================================================
-- 20_rx_by_class.sql
-- Build mart_rx_by_class: Oregon Medicaid prescriptions per QUARTER for the
-- addiction-treatment / harm-reduction drug classes relevant to Measure 110.
--
-- Crosswalk note: SDUD product names are truncated (~10 chars) and inconsistently
-- cased, so we match with ILIKE (case-insensitive). Brand names roll up to class:
--   buprenorphine_moud <- BUPRENOR, SUBOXONE, ZUBSOLV, SUBLOCADE
--   naltrexone_moud    <- NALTREXONE, VIVITROL
--   naloxone           <- NALOXONE, NARCAN
--   methadone          <- METHADONE  (note: pharmacy methadone is mostly for pain)
-- ============================================================

DROP TABLE IF EXISTS mart_rx_by_class;

CREATE TABLE mart_rx_by_class AS
WITH labeled AS (                                   -- tag each row with a drug class
    SELECT
        year,
        quarter,
        number_of_prescriptions,
        CASE
            WHEN product_name ILIKE 'BUPRENOR%' OR product_name ILIKE 'SUBOX%'
              OR product_name ILIKE 'ZUBSOLV%'  OR product_name ILIKE 'SUBLOCAD%' THEN 'buprenorphine_moud'
            WHEN product_name ILIKE 'NALTREX%'  OR product_name ILIKE 'VIVITROL%' THEN 'naltrexone_moud'
            WHEN product_name ILIKE 'NALOX%'    OR product_name ILIKE 'NARCAN%'   THEN 'naloxone'
            WHEN product_name ILIKE 'METHADON%'                                   THEN 'methadone'
        END AS drug_class
    FROM sdud_or
)
SELECT
    year,
    quarter,
    make_date(year, quarter * 3 - 2, 1) AS quarter_start,   -- real date for Tableau's time axis
    drug_class,
    SUM(number_of_prescriptions)        AS total_prescriptions
FROM labeled
WHERE drug_class IS NOT NULL                         -- keep only the classes we tagged
GROUP BY year, quarter, drug_class
ORDER BY drug_class, year, quarter;
