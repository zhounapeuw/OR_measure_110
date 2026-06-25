# Measure 110 — Data Download Checklist (missing items)

Generated 2026-06-24. Tracks gaps found in the collected data folders.

## 1. MMA_enrollment (Oregon OHA / OHP monthly enrollment)

Source: https://www.oregon.gov/oha/HSD/OHP/Pages/Reports.aspx
Dashboard + current Excel: https://www.oregon.gov/oha/hpa/analytics/pages/medicaid-enrollment.aspx

IMPORTANT: OHA overwrites this file each month — only the current month is posted,
so the missing months below are NOT downloadable from the live page. Recovery options,
in order of effort:

1. Wayback Machine — best bet for the exact historical .xls. Look up the file/page URL
   at https://web.archive.org/ for snapshots dated in each missing month. Try the
   reports page and the direct file URL pattern from a file you already have.
2. Power BI dashboard — check whether it lets you filter to a past month and export;
   may reconstruct the numbers even if not the original file layout.
3. Public records / data request — email OHA.HealthAnalyticsRequest@oha.oregon.gov
   for the specific missing months (canonical path for historical OHP data).

Missing months (save as `MMA_enrollment_YYYYMM.xls`):
- [ ] 2020-09
- [ ] 2021-01
- [ ] 2021-05
- [ ] 2021-12
- [ ] 2022-06
- [ ] 2022-10
- [ ] 2022-11
- [ ] 2023-11
- [ ] 2023-12
- [ ] 2025-01
- [ ] 2025-07
- [ ] 2025-08
- [ ] 2025-10
- [ ] 2025-11
- [ ] 2026-03
- [ ] 2026-04

(2019 and 2024 are complete. 2026-06 likely not yet published.)

## 2. SAMHSA — substance-use baseline (N-SSATS)

Your 2019 & 2020 files are N-MHSS (mental health only). The substance-use facility
counterpart for those years is N-SSATS. Grab the public-use data files:
- [ ] N-SSATS 2019: https://www.datafiles.samhsa.gov/dataset/national-survey-substance-abuse-treatment-services-2019-n-ssats-2019-ds0001
- [ ] N-SSATS 2020: https://www.samhsa.gov/data/data-we-collect/n-sumhss-national-substance-use-and-mental-health-services-survey/datafiles/n-ssats-2020
- Landing (all years): https://www.samhsa.gov/data/data-we-collect/n-sumhss-national-substance-use-and-mental-health-services-survey

(2021+ N-SUMHSS already combines substance use + mental health, so no N-SSATS needed there.)

Housekeeping:
- [ ] Unzip the 2020/2021/2022/2023 bundles (only 2019 and 2024 are currently extracted).

## 3. cdc_wonder — overdose deaths (query-generated, no static file)

Run via Multiple Cause of Death, 2018-2024, Single Race:
https://wonder.cdc.gov/mcd-icd10-expanded.html

Query setup to reproduce existing files: Location = Oregon; Years = 2019-2024;
group by Year; MCD = the relevant T-code. Export each as CSV.

Missing categories:
- [ ] All-drug overdose total (any MCD in T36-T50.8) — overall trend / denominator
- [ ] T40.0 Opium
- [ ] T40.6 Other & unspecified narcotics

(Already have: T40.1 heroin, T40.2 other opioids, T40.3 methadone,
T40.4 other synthetic narcotics, T40.5 cocaine, T43.6 psychostimulants/meth.)

## 4. sdud (Medicaid State Drug Utilization Data)

Complete, 2018-2025. No action. (Source: https://www.medicaid.gov/medicaid/prescription-drugs/state-drug-utilization-data)

## 5. Time resolution & harmonization

Native resolutions, verified against the files (2026-06-24):
- OHA dual enrollment: MONTHLY — a *stock* (point-in-time count).
- SDUD: QUARTERLY (`Year` + `Quarter` columns) — a *flow* within the quarter.
- CDC WONDER overdose: already MONTHLY (`Year`/`Month` rows). NOTE: files actually
  span 2018-2024 (not 2019-2024 as the filename says); counts only, no rates/population.
- SAMHSA N-SUMHSS/N-SSATS: ANNUAL — one point-in-time survey per year; cannot be finer.

Plan: standardize the time-varying series to QUARTERLY (coarsest native cadence = SDUD).
This supports an interrupted-time-series design around Measure 110 (effective 2021-02-01)
and recriminalization (HB 4002, effective 2024-09-01).
- Enrollment (stock): use quarter-end or quarter-average; do NOT sum the 3 months.
- SDUD (flow): already quarterly.
- CDC overdose (flow): re-pull, see suppression note.
- SAMHSA: keep ANNUAL; use as a yearly context covariate aligned by year. Do not upsample.

CDC WONDER suppression — important:
- WONDER has NO "Quarter" grouping (Year and Month are the only time options), so you
  cannot ask it for quarterly cells directly.
- The monthly files are heavily suppressed: "Suppressed" = a true count of 1-9 (hidden
  for confidentiality), NOT zero and NOT missing. Do not drop these cells when summing.
- [ ] Aggregate the monthly files you already have (2018-2024) to quarters in code,
      bounding suppressed months: low = sum(known) + 1*nSuppressed;
      high = sum(known) + 9*nSuppressed; point ~ sum(known) + 5*nSuppressed.
      Carry low/high as an uncertainty band.
- [ ] OPTIONAL alternative: re-pull from https://wonder.cdc.gov/mcd-icd10-expanded.html
      grouped by Year only, restricting included months to one quarter, run 4x. Only works
      if the form exposes a month selection list. Thin categories may still suppress.
- [ ] If you want rates (not just counts), add Population on any re-pull.

Do NOT interpolate coarse -> fine (e.g., SAMHSA annual -> quarterly) for any inferential
model: it fabricates observations and understates uncertainty / inflates significance.
Interpolation is acceptable only for visual trend lines, never as input rows to a
significance test or ITS regression.
