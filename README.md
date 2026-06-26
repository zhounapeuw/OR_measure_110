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

This creates/updates `db/measure110.duckdb`, runs every `.sql` file in
`sql/` in order, and writes Tableau CSVs to `exports/`.

## Postgres / Tableau (live connection)

The analysis-ready mart tables are also published to a local PostgreSQL server so
Tableau Desktop can connect live (the 4 GB of raw data stays in DuckDB).

```bash
# 1. Start the server (after a reboot). Or double-click start_postgres.bat
pg_ctl -D pgdata -l pgdata/server.log start

# 2. After rebuilding the marts, push them to Postgres
python publish_to_postgres.py
```

Tableau Desktop -> Connect -> PostgreSQL:
`localhost` / port `5432` / database `measure110` / user `postgres` / password `postgres`.

(First-time server setup: `initdb -D pgdata -U postgres ...` then `createdb measure110`.
Already done on this machine; `pgdata/` is git-ignored.)

## Project layout

```
build_db.py            # runs the .sql files; builds DuckDB + CSV exports
publish_to_postgres.py # copies the mart tables from DuckDB into PostgreSQL
sql/                   # the SQL, as plain readable files (run in name order)
  01_raw_views.sql     #   views pointing at the raw source files
  02_cdc_views.sql     #   CDC deaths + population
  03_overdose_rate.sql #   annual overdose rate per 100k (mart_overdose_rate)
  99_export.sql        #   write marts to exports/ for Tableau
db/measure110.duckdb   # the DuckDB database (built by build_db.py)
exports/               # Tableau-ready CSVs (regenerated each build)
pgdata/                # local PostgreSQL data cluster (git-ignored)
explore.ipynb          # exploration notebook (tables + charts)
sdud/ cdc_wonder/ MMA_enrollment/ SAMHSA/   # raw data
DATA_CHECKLIST.md      # data inventory, gaps, and harmonization plan
```

## Status

- [x] Data collected (4 sources) and inventoried
- [x] DuckDB set up; SDUD readable via `raw_sdud`
- [x] CDC deaths + population views; annual overdose rate per 100k (`mart_overdose_rate`)
- [x] Tableau feed: CSV export + live PostgreSQL connection
- [ ] Quarterly aggregation of the overdose series
- [ ] Enrollment and SAMHSA loaders
- [ ] SDUD drug-class crosswalk (opioids, MOUD, naloxone, stimulants)
- [ ] Quarterly Oregon panel (`mart_quarterly_panel`)
- [ ] Interrupted-time-series analysis + validation
