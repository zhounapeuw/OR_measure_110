-- ============================================================
-- 10_overdose_rate.sql
-- Build mart_overdose_rate: annual Oregon overdose death rate per 100,000
-- by drug (2018-2024).
--
-- Suppressed months hide a true count of 1-9, so we carry a band:
--   deaths_est = known + 5 * suppressed   (midpoint)
--   low/high   = known + 1 or 9 * suppressed
-- Re-running this file rebuilds the table from scratch (DROP + CREATE).
-- ============================================================

DROP TABLE IF EXISTS mart_overdose_rate;

CREATE TABLE mart_overdose_rate AS
WITH annual AS (                                    -- monthly -> annual per drug
    SELECT
        drug,
        year,
        COALESCE(SUM(deaths_known), 0)        AS known_deaths,
        COUNT(*) FILTER (WHERE is_suppressed) AS suppressed_months
    FROM overdose_deaths
    GROUP BY drug, year
)
SELECT
    a.year,
    a.drug,
    a.known_deaths + 5 * a.suppressed_months AS deaths_est,
    a.suppressed_months,
    p.population,
    ROUND((a.known_deaths + 5 * a.suppressed_months) * 100000.0 / p.population, 1) AS rate_per_100k,
    ROUND((a.known_deaths + 1 * a.suppressed_months) * 100000.0 / p.population, 1) AS rate_low,
    ROUND((a.known_deaths + 9 * a.suppressed_months) * 100000.0 / p.population, 1) AS rate_high
FROM annual a
JOIN population p ON p.year = a.year
WHERE a.year BETWEEN 2018 AND 2024
ORDER BY a.drug, a.year;
