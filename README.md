# Oregon Measure 110 — Drug Use & Medicaid Analysis

Analysis of drug-related outcomes in Oregon around Measure 110 (drug
decriminalization, effective 2021-02-01) and its partial rollback under
HB 4002 (recriminalization, effective 2024-09-01).

## Pipeline

```
raw files (data/)  →  Python loaders  →  PostgreSQL (staging → marts)  →  Tableau
```
Thin Python loaders extract and lightly clean the raw source files into Oregon-only
staging CSVs; PostgreSQL does all the transformation/analysis SQL and serves the
result tables to Tableau Desktop over a live connection.

## Data sources

| Folder | Source | What it is | Cadence |
|--------|--------|------------|---------|
| `data/sdud/` | Medicaid State Drug Utilization Data (CMS) | Prescriptions reimbursed by Medicaid, per drug | Quarterly, 2018–2025 |
| `data/cdc_wonder/` | CDC WONDER Multiple Cause of Death | Oregon overdose deaths by drug category + population | Monthly, 2018–2024 |
| `data/MMA_enrollment/` | Oregon OHA / OHP | Medicare–Medicaid dual-eligible enrollment | Monthly |
| `data/SAMHSA/` | SAMHSA N-MHSS / N-SUMHSS | Treatment-facility surveys | Annual, 2019–2024 |

See `DATA_CHECKLIST.md` for known gaps, source URLs, and the plan to harmonize
everything to a quarterly Oregon panel.

## Setup

- **Python:** the `measure_110` conda environment (Python 3.12) — used for the
  loaders and the `psql` client.
  ```bash
  conda activate measure_110
  ```
- **PostgreSQL 17** installed via the EnterpriseDB installer, running as the Windows
  service `postgresql-x64-17` (auto-starts at boot). Connection:
  `host=127.0.0.1 port=5432 dbname=measure110 user=postgres password=postgres`.

## How to run

```bash
# 1. Stage the raw data (Oregon-only) into staging/
python loaders/load_sdud.py
#    (more loaders to come: CDC deaths/population, enrollment, SAMHSA)

# 2. Load + transform in PostgreSQL
#    Create tables and load the staging CSVs with \copy, then run the sql/ files.
#    (A build script will tie steps 1–2 together as the pipeline grows.)
```

## Tableau (live connection)

Tableau Desktop → Connect → PostgreSQL:
`127.0.0.1` / port `5432` / database `measure110` / user `postgres` / password `postgres`.
Connect to the mart tables (or use Custom SQL).

## Project layout

```
loaders/               # thin Python extract/clean -> staging CSVs
  load_sdud.py         #   SDUD: filter to Oregon, combine 8 years
sql/                   # PostgreSQL transformation & analysis SQL (run in name order)
staging/               # Oregon-only staging CSVs (git-ignored; regenerate via loaders)
data/                  # raw source files (git-ignored): sdud, cdc_wonder, MMA_enrollment, SAMHSA
explore.ipynb          # exploration notebook (charts) — to be repointed to Postgres
DATA_CHECKLIST.md      # data inventory, gaps, and harmonization plan
```

## Status

- [x] Data collected (4 sources) and inventoried, consolidated under `data/`
- [x] PostgreSQL (EDB) running as a service; `measure110` database created
- [x] SDUD loader → Oregon-only staging CSV
- [ ] Load SDUD into Postgres (`sdud_or` table)
- [ ] CDC loader (deaths + population) + overdose rate mart, in Postgres SQL
- [ ] Enrollment and SAMHSA loaders
- [ ] SDUD drug-class crosswalk (opioids, MOUD, naloxone, stimulants)
- [ ] Quarterly Oregon panel
- [ ] Interrupted-time-series analysis + validation
