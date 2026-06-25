-- ============================================================
-- 03_overdose_rate.sql
-- Oregon overdose deaths per 100,000, by drug and year (2018-2024).
--
-- Suppressed months hide a true count of 1-9. We don't drop them; we carry
-- a low/high band:  low  = known + 1 * (#suppressed months)
--                   high = known + 9 * (#suppressed months)
--                   est  = known + 5 * (#suppressed months)   <- midpoint
-- ============================================================

-- Step 1: roll the monthly deaths up to annual totals, with the bounds.
CREATE OR REPLACE VIEW stg_overdose_annual AS
SELECT
    drug,
    year,
    COALESCE(SUM(deaths_known), 0)        AS deaths_known,      -- non-suppressed months
    SUM(is_suppressed::INT)               AS suppressed_months,
    COALESCE(SUM(deaths_known), 0) + 1 * SUM(is_suppressed::INT) AS deaths_low,
    COALESCE(SUM(deaths_known), 0) + 5 * SUM(is_suppressed::INT) AS deaths_est,
    COALESCE(SUM(deaths_known), 0) + 9 * SUM(is_suppressed::INT) AS deaths_high
FROM stg_overdose_deaths
GROUP BY drug, year;

-- Step 2: join population and compute the rate per 100,000.
CREATE OR REPLACE TABLE mart_overdose_rate AS
SELECT
    d.year,
    d.drug,
    d.deaths_est,
    d.suppressed_months,
    p.population,
    ROUND(d.deaths_est  * 100000.0 / p.population, 1) AS rate_per_100k,
    ROUND(d.deaths_low  * 100000.0 / p.population, 1) AS rate_low,
    ROUND(d.deaths_high * 100000.0 / p.population, 1) AS rate_high
FROM stg_overdose_annual d
JOIN stg_population p USING (year)
WHERE d.year BETWEEN 2018 AND 2024      -- complete years that have a population figure
ORDER BY d.drug, d.year;
