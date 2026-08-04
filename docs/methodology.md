# Methodology & decisions

The analytical choices behind the project and *why* they were made. The goal is that
every non-obvious decision is defensible and reproducible. A dated decision log at the
bottom records changes as the project evolves.

## Research question

Did drug-related outcomes in Oregon change around **Measure 110** (decriminalization,
effective **2021-02-01**) and its partial rollback under **HB 4002** (recriminalization,
effective **2024-09-01**)? Two sides:
- **Harm:** overdose death rates (CDC WONDER).
- **Response:** treatment access and harm reduction — MOUD and naloxone prescriptions
  (Medicaid SDUD).

## Key decisions

**Architecture — Python loaders → PostgreSQL → Tableau (no DuckDB).**
Raw files are extracted/cleaned by thin Python loaders into staging CSVs; PostgreSQL does
all transformation/analysis SQL; Tableau connects live. DuckDB was used early but removed
in favor of a single, recruiter-recognizable engine. Trade-off: Postgres can't read the
raw files directly (footers, `.xls`, 4 GB), so loaders do the extraction — normal for a
Postgres shop.

**Oregon-only.** SDUD is national (~6M rows); loaders filter to Oregon during staging
(~750k rows) so Postgres stays small and fast. The project is Oregon-specific.

**CDC suppression — bounds, never dropped.** CDC hides death counts of 1–9 (`Suppressed`).
Dropping them would undercount. Instead each suppressed month is carried as a band:
low = +1, midpoint = +5, high = +9 per suppressed month. The midpoint feeds the headline
`rate_per_100k`; `rate_low`/`rate_high` carry the uncertainty.

**Denominators / population.** Rates use annual Oregon population (July-1 estimates) from
**CDC WONDER**, the same source as the deaths, so numerator and denominator are consistent
with CDC's own published rates. No official monthly/quarterly population exists; for finer
grains, annual figures are interpolated — acceptable for a smooth quantity like population,
but **never** interpolate coarse outcome data up into an inferential model.

**Time resolution.** Native grains differ (SDUD quarterly, CDC monthly, SAMHSA annual,
enrollment monthly). Plan: harmonize the time-varying series to **quarterly** for the
panel. Aggregation respects stock vs flow — enrollment is a *stock* (average/period-end),
deaths and prescriptions are *flows* (sum). The overdose-rate mart is currently annual;
a quarterly version is planned.

**Rates are crude, not age-adjusted** — a known limitation; fine for within-state trends.

**Causal caution.** This is descriptive / interrupted-time-series, not proof of causation.
The overdose rise is dominated by a **national fentanyl supply shock** that confounds any
simple Measure-110 attribution — this must be acknowledged in any conclusion.

## Documentation convention (going forward)

- Every new table → an entry in [`data_dictionary.md`](data_dictionary.md).
- Every non-obvious analytical choice → a dated entry in the decision log below.
- Any name/code mapping (crosswalk) → its own note in `docs/` (e.g. `drug_crosswalk.md`).

## Decision log

- **2026-06-24** — Chose DuckDB for fast local prototyping; built overdose-rate mart.
- **2026-06-24** — Suppression handled as 1/5/9 bounds rather than dropping suppressed cells.
- **2026-06-25** — Migrated to all-PostgreSQL (loaders → Postgres → Tableau); removed DuckDB
  for a single recognizable engine. Consolidated raw data under `data/`.
- **2026-06-25** — Installed PostgreSQL 17 via the EDB installer as a Windows service after
  the conda build hit a Windows shared-memory (error 487) failure.
- **2026-06-25** — Built `mart_rx_by_class`; documented the SDUD product-name → drug-class
  crosswalk and its caveats in `drug_crosswalk.md`.
- **2026-07-13** — **Buprenorphine "6x decline" was an artifact — two bugs found and fixed.**
  SDUD appeared to show buprenorphine prescriptions collapsing 6x (2018-2025), which contradicts
  national trends. Diagnosis: (a) *not* a managed-care reporting dropout — FFS and MCOU both fell
  together; (b) *not* dataset-wide — total Oregon SDUD prescriptions were stable/rising; (c) SAMHSA's
  independent buprenorphine client census was flat, not collapsing. Root causes:
    1. **Crosswalk gap** — product naming changed; `BUPREN&NAL`, `BUP/NAL*`, `BRIXADI` were missed
       (~18k Rx in 2024 alone). Patterns fixed in `sql/20_rx_by_class.sql`.
    2. **Wrong metric (the big one)** — `number_of_prescriptions` counts *fills*, and buprenorphine
       dispensing shifted from weekly to monthly (units per Rx: 9.3 → 47.7), so fills fell ~5x while
       `units_reimbursed` stayed flat. **Decision: `units_reimbursed` is the treatment-access metric;
       prescription counts are NOT comparable over time.**
  Corrected trend: buprenorphine dispensing rose ~2x from 2018 to a **2021–2022 peak**, then
  declined through 2025. Lesson recorded in `drug_crosswalk.md`.
- **2026-07-23** — **CCO SUD-treatment findings (2024, IET 18+).** (a) *System-wide shortfall:*
  all 16 CCOs are below the 48.6% initiation benchmark (statewide 41.7%). (b) *Rural gap confirmed*
  directly from OHA's Frontier/Rural/Urban breakout — initiation Urban 43.3% vs Frontier/Rural 38.8%;
  engagement gradient Frontier 14.0% < Rural 15.2% < Urban 17.3%. (c) *Two-dimensional need:*
  initiation and engagement decouple across CCOs (some connect people but lose them, others the
  reverse) — so "support" must be targeted (outreach vs. retention). Built `cco_county_iet`
  (per-county IET, latest year) for choropleth maps.
  - *Access-profile map thresholds:* the 4-way county classification (top-priority / low-initiation /
    low-engagement / above-avg) splits at the **statewide 2024 rates — Initiation 41.7%, Engagement
    16.5%** (i.e. below/above the Oregon average). Chosen over the incentive benchmark (48.6%/18.1%)
    because ~all counties fall below the initiation benchmark, which would make the map uninformative.
- **2026-07-22** — Added **OHA CCO Metrics** (Overall Population) as `cco_metrics` for a
  CCO-level treatment-access / equity analysis. The SUD measure is **Initiation &
  Engagement of SUD Treatment (IET, NQF 0004)**; the incentivized **18+** variants
  (`IET_INI_18`, `IET_ENG_18`) exist **2019–2024** only (CCO 2.0 era) — the older CCO-1.0
  SUD measure was SBIRT (screening, not comparable). Decision: **Layer 2 is cross-sectional**
  ("which CCOs/regions/populations need more support"), not a long trend — the ~2 pre-110
  years (2019–20) are too thin for a before/after, and SDUD carries the long treatment trend.
  Denominators are statewide-only (member confidentiality). Demographic + Geographic
  disparity workbooks (the equity strata) are staged in `data/CCO/` for a follow-up.
- **2026-07-13** — Two data-handling decisions on `mart_rx_by_class`:
  (a) **2022 Q3 buprenorphine set to NULL** — an isolated SDUD data hole (~771 units vs ~1.3M in
      neighboring quarters, buprenorphine-specific; naloxone/naltrexone are normal that quarter,
      so it's not a whole-quarter Oregon gap — likely one CCO's claims missing). Nulled in the mart
      so it reads as missing rather than a false crash.
  (b) **Medicaid "unwinding" is a confounder for post-2023 measures.** Pandemic continuous Medicaid
      enrollment ended April 2023, disenrolling many Oregonians. SDUD sees only *Medicaid* claims, so
      declines from 2023 on may reflect fewer enrollees, not less per-person treatment. Interpret
      2023+ Medicaid measures with this caveat; consider normalizing per-enrollee via enrollment data.
- **2026-06-27** — Confirmed via the N-SSATS 2019 codebook that the `*BUPNUM` MOUD client
  variables are **banded categories** (e.g. `OPBUPNUM`: 1=0–4, 2=5–10, 3=11–20, 4=21–50,
  5=51+), with band cutoffs that differ by setting — whereas N-SUMHSS (2021+) records raw
  counts under the same column names. Decisions: (a) do NOT splice SAMHSA buprenorphine
  client counts across the 2021 N-SSATS→N-SUMHSS break — the count trend is N-SUMHSS
  2021–2024 only; (b) SDUD prescriptions remain the primary, fully-comparable treatment-
  access measure; (c) the lowest band `1` includes 0, so "offers buprenorphine" presence
  must come from a dedicated use flag, not from `*BUPNUM ≥ 1`.
