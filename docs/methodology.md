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
