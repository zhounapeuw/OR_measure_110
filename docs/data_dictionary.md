# Data dictionary

Every source file, staging file, and PostgreSQL table in the project, with column
meanings. Tables marked *(mart)* are analysis-ready outputs; the rest are inputs.

## Raw source files (`data/`, git-ignored)

### `data/sdud/*.csv` — CMS State Drug Utilization Data (8 yearly files, 2018–2025)
Medicaid-reimbursed prescriptions, one row per drug (NDC) per state per quarter per
utilization type. Key columns: `Utilization Type` (FFSU = fee-for-service, MCOU =
managed care), `State`, `NDC`, `Year`, `Quarter`, `Suppression Used`, `Product Name`
(truncated ~10 chars), `Units Reimbursed`, `Number of Prescriptions`,
`Total/Medicaid/Non Medicaid Amount Reimbursed`.

### `data/cdc_wonder/OR overdose deaths*.csv` — CDC WONDER Multiple Cause of Death (6 files)
One file per drug category (heroin, rx_opioids, methadone, synthetic/fentanyl, cocaine,
methamphetamine). Monthly Oregon death counts, 2018–2024 (plus provisional later).
`Deaths` is a count or the literal `Suppressed` (true count 1–9 hidden). A notes/caveats
footer is skipped by the loader.

### `data/cdc_wonder/*population*.xls` — Oregon population
Tab-delimited (despite `.xls`). Annual Oregon population (July 1 estimates), 2018–2024.
Only the `Year`/`Population` columns are used.

### `data/MMA_enrollment/*.xls` — Oregon OHA dual-eligible enrollment *(not yet loaded)*
Multi-sheet Excel workbooks; monthly Medicare–Medicaid dual-eligible OHP counts.

### `data/SAMHSA/*` — SAMHSA facility surveys *(not yet loaded)*
N-MHSS (2019–20) / N-SUMHSS (2021–24); annual treatment-facility census.

## Staging files (`staging/`, git-ignored — produced by `loaders/`)

| File | Loader | Columns |
|---|---|---|
| `sdud_or.csv` | `load_sdud.py` | same 15 columns as raw SDUD, Oregon rows only |
| `overdose_deaths.csv` | `load_cdc.py` | `drug, year, month, is_suppressed, deaths_known` |
| `population.csv` | `load_cdc.py` | `year, population` |

## PostgreSQL tables (database `measure110`)

### `sdud_or` — built by `sql/00_create_tables.sql`
Oregon Medicaid prescriptions. 15 columns (snake_case versions of the SDUD columns).
`number_of_prescriptions` is NULL where the source suppressed the value.

### `overdose_deaths` — `sql/00_create_tables.sql`
| column | type | meaning |
|---|---|---|
| `drug` | text | drug category (heroin, rx_opioids, methadone, synthetic_opioids_fentanyl, cocaine, methamphetamine) |
| `year`, `month` | int | period |
| `is_suppressed` | bool | true = CDC hid the count (true value 1–9) |
| `deaths_known` | int | death count, NULL when suppressed |

### `population` — `sql/00_create_tables.sql`
| column | type | meaning |
|---|---|---|
| `year` | int | calendar year |
| `population` | bigint | Oregon population (CDC/Census July-1 estimate) |

### `mart_overdose_rate` *(mart)* — `sql/10_overdose_rate.sql`
Annual overdose death **rate per 100,000** by drug, 2018–2024.
| column | meaning |
|---|---|
| `year`, `drug` | period and drug category |
| `deaths_est` | known deaths + 5 × suppressed months (midpoint estimate) |
| `suppressed_months` | # months suppressed that year |
| `population` | year's Oregon population |
| `rate_per_100k` | `deaths_est / population × 100000` |
| `rate_low`, `rate_high` | bounds using 1× and 9× suppressed months |

### `mart_rx_by_class` *(mart)* — `sql/20_rx_by_class.sql`
Oregon Medicaid prescriptions per **quarter** for treatment/harm-reduction classes.
See [`drug_crosswalk.md`](drug_crosswalk.md) for the name→class mapping.
| column | meaning |
|---|---|
| `year`, `quarter` | period |
| `quarter_start` | first day of the quarter (a real date, for Tableau) |
| `drug_class` | buprenorphine_moud, naltrexone_moud, naloxone, methadone |
| `total_prescriptions` | summed prescriptions in that class/quarter |
