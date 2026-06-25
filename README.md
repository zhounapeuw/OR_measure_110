# Oregon Measure 110 — Drug Use & Medicaid Analysis

Analysis of drug-related outcomes in Oregon around Measure 110 (drug
decriminalization, effective 2021-02-01) and its partial rollback under
HB 4002 (recriminalization, effective 2024-09-01).

## Data sources

| Folder | Source | What it is | Cadence |
|--------|--------|------------|---------|
| `sdud/` | Medicaid State Drug Utilization Data (CMS) | Prescriptions reimbursed by Medicaid, per drug | Quarterly, 2018–2025 |
| `cdc_wonder/` | CDC WONDER Multiple Cause of Death | Oregon overdose deaths by drug category + population | Monthly, 2018–2024 |
| `MMA_enrollment/` | Oregon OHA / OHP | Medicare–Medicaid dual-eligible enrollment | Monthly |
| `SAMHSA/` | SAMHSA N-MHSS / N-SUMHSS | Treatment-facility surveys | Annual, 2019–2024 |

See `DATA_CHECKLIST.md` for known gaps, source URLs, and the plan to harmonize
everything to a quarterly Oregon panel.

## Setup

Uses the `measure_110` conda environment (Python 3.12):

```bash
conda activate measure_110
pip install duckdb        # if not already installed
```

## How to run

```bash
python build_db.py
```

This creates/updates `db/measure110.duckdb` and runs every `.sql` file in
`sql/` in order. It prints a sanity check at the end.

## Project layout

```
build_db.py          # runs the .sql files against the database
sql/                 # the SQL, as plain readable files (run in name order)
  01_raw_views.sql   #   views pointing at the raw source files
db/measure110.duckdb # the database file (built by build_db.py)
sdud/ cdc_wonder/ MMA_enrollment/ SAMHSA/   # raw data
DATA_CHECKLIST.md    # data inventory, gaps, and harmonization plan
```

## Status

- [x] Data collected (4 sources) and inventoried
- [x] DuckDB set up; SDUD readable via `raw_sdud`
- [ ] Views for CDC deaths + population; overdose rate per 100k
- [ ] Enrollment and SAMHSA loaders
- [ ] Quarterly Oregon panel (`mart_quarterly_panel`)
- [ ] Interrupted-time-series analysis + validation
