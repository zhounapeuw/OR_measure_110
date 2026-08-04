-- ============================================================
-- 20_rx_by_class.sql
-- Build mart_rx_by_class: Oregon Medicaid MOUD / harm-reduction drugs per QUARTER.
--
-- *** TWO CRITICAL LESSONS BAKED IN (see docs/methodology.md, 2026-07-13) ***
--
-- 1. USE total_units, NOT total_prescriptions, FOR TRENDS.
--    number_of_prescriptions counts FILLS. Buprenorphine dispensing shifted from
--    weekly to monthly fills (units per Rx rose 9.3 -> 47.7 from 2018 to 2025), so
--    prescription counts fell ~5x while the actual drug dispensed stayed flat.
--    Counting fills would falsely show treatment "collapsing." units_reimbursed
--    (quantity dispensed) is immune to fill-frequency changes. Both are kept below
--    for transparency, but total_units is the analysis metric.
--
-- 2. CROSSWALK MUST CATCH RENAMED PRODUCTS.
--    Product naming changed over time: generic buprenorphine/naloxone appears as
--    BUPREN&NAL and BUP/NAL in later years (plus the newer BRIXADI injectable).
--    Missing them undercounted recent years. Verified NOT buprenorphine and
--    correctly excluded: BUPROPION (antidepressant), IBUPROFEN, BUPIVACAINE.
-- ============================================================

DROP TABLE IF EXISTS mart_rx_by_class;

CREATE TABLE mart_rx_by_class AS
WITH labeled AS (                                   -- tag each row with a drug class
    SELECT
        year,
        quarter,
        number_of_prescriptions,
        units_reimbursed,
        CASE
            WHEN product_name ILIKE 'BUPRENOR%' OR product_name ILIKE 'BUPREN&%'
              OR product_name ILIKE 'BUP/NAL%'  OR product_name ILIKE 'SUBOX%'
              OR product_name ILIKE 'ZUBSOLV%'  OR product_name ILIKE 'SUBLOCAD%'
              OR product_name ILIKE 'BRIXADI%'                                    THEN 'buprenorphine_moud'
            WHEN product_name ILIKE 'NALTREX%'  OR product_name ILIKE 'VIVITROL%' THEN 'naltrexone_moud'
            WHEN product_name ILIKE 'NALOX%'    OR product_name ILIKE 'NARCAN%'
              OR product_name ILIKE 'KLOXXADO%'                                   THEN 'naloxone'
            WHEN product_name ILIKE 'METHADON%'                                   THEN 'methadone'
        END AS drug_class
    FROM sdud_or
)
SELECT
    year,
    quarter,
    make_date(year, quarter * 3 - 2, 1) AS quarter_start,   -- real date for Tableau's time axis
    drug_class,
    -- 2022 Q3 buprenorphine is an isolated SDUD data hole (missing claims: ~771 units vs ~1.3M in
    -- neighboring quarters; naloxone/naltrexone that quarter are normal). NULL it so it reads as
    -- "missing" (a gap in the line / excluded from stats) rather than a false ~99% crash.
    CASE WHEN drug_class = 'buprenorphine_moud' AND year = 2022 AND quarter = 3 THEN NULL
         ELSE SUM(units_reimbursed) END        AS total_units,        -- <-- USE THIS for trends
    CASE WHEN drug_class = 'buprenorphine_moud' AND year = 2022 AND quarter = 3 THEN NULL
         ELSE SUM(number_of_prescriptions) END AS total_prescriptions -- fills; distorted by fill frequency
FROM labeled
WHERE drug_class IS NOT NULL
GROUP BY year, quarter, drug_class
ORDER BY drug_class, year, quarter;
