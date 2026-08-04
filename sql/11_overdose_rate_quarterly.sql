-- ============================================================
-- 11_overdose_rate_quarterly.sql
-- Build mart_overdose_rate_quarterly: Oregon overdose death rate per 100,000 by
-- drug and QUARTER (2018-2024). The quarterly grain lets the series line up with
-- Measure 110 (2021-02) and HB 4002 (2024-09) instead of burying them mid-year.
--
-- Same suppression-bounds logic as 10_overdose_rate.sql (deaths_est = known + 5x
-- suppressed months; low/high use 1x and 9x). The rate is PER-QUARTER: quarterly
-- deaths / that year's population (population is annual). Well-populated drugs
-- (fentanyl, meth) are clean at this grain; heavily-suppressed ones (heroin,
-- cocaine, methadone) have wide bounds -- interpret those with care.
-- Provisional years (2025-26) drop out automatically: population has no rows there.
-- ============================================================

DROP TABLE IF EXISTS mart_overdose_rate_quarterly;

CREATE TABLE mart_overdose_rate_quarterly AS
WITH quarterly AS (                                 -- monthly -> quarterly per drug
    SELECT
        drug,
        year,
        ((month - 1) / 3) + 1                  AS quarter,   -- months 1-3 -> Q1, 4-6 -> Q2, ...
        COALESCE(SUM(deaths_known), 0)          AS known_deaths,
        COUNT(*) FILTER (WHERE is_suppressed)   AS suppressed_months   -- 0-3 per quarter
    FROM overdose_deaths
    GROUP BY drug, year, ((month - 1) / 3) + 1
)
SELECT
    q.year,
    q.quarter,
    make_date(q.year, q.quarter * 3 - 2, 1)         AS quarter_start,   -- real date for Tableau
    q.drug,
    q.known_deaths + 5 * q.suppressed_months        AS deaths_est,
    q.suppressed_months,
    p.population,
    ROUND((q.known_deaths + 5 * q.suppressed_months) * 100000.0 / p.population, 2) AS rate_per_100k_qtr,
    ROUND((q.known_deaths + 1 * q.suppressed_months) * 100000.0 / p.population, 2) AS rate_low,
    ROUND((q.known_deaths + 9 * q.suppressed_months) * 100000.0 / p.population, 2) AS rate_high
FROM quarterly q
JOIN population p ON p.year = q.year
ORDER BY q.drug, q.year, q.quarter;
