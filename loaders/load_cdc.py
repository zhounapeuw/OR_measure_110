"""
loaders/load_cdc.py - stage the CDC WONDER data for Postgres.

Produces two tidy staging files:
  staging/overdose_deaths.csv  - one row per drug-month, with a suppression flag
  staging/population.csv        - Oregon population per year

The raw death files (data/cdc_wonder/OR overdose deaths*.csv) have a notes/caveats
footer and a "Deaths" column that mixes numbers with the word "Suppressed". The
population file is tab-delimited with its own footer. We skip the footers and keep
suppressed months (flagged, not dropped) so the SQL can carry low/high bounds later.

Usage (measure_110 env active):
    python loaders/load_cdc.py
"""

import glob
import os
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
Path("staging").mkdir(exist_ok=True)


def drug_from_filename(name: str) -> str:
    n = name.lower()
    if "cocaine" in n:           return "cocaine"
    if "psychostim_meth" in n:   return "methamphetamine"
    if "heroin" in n:            return "heroin"
    if "methadone" in n:         return "methadone"
    if "other_opioids" in n:     return "rx_opioids"
    if "other_synth_narc" in n:  return "synthetic_opioids_fentanyl"
    return "unknown"


# --- overdose deaths (6 files) ---
parts = []
for path in sorted(glob.glob("data/cdc_wonder/OR overdose deaths*.csv")):
    df = pd.read_csv(path, dtype=str, engine="python", on_bad_lines="skip")
    # keep only real monthly data rows (drops footer rows)
    df = df[df["Month Code"].astype(str).str.match(r"^\d{4}/\d{2}$", na=False)].copy()
    df["drug"] = drug_from_filename(os.path.basename(path))
    df["year"] = df["Year Code"].str.strip().astype(int)
    df["month"] = df["Month Code"].str.split("/").str[1].astype(int)
    df["is_suppressed"] = df["Deaths"].eq("Suppressed")
    df["deaths_known"] = pd.to_numeric(df["Deaths"], errors="coerce").astype("Int64")
    parts.append(df[["drug", "year", "month", "is_suppressed", "deaths_known"]])

deaths = pd.concat(parts, ignore_index=True)
deaths.to_csv("staging/overdose_deaths.csv", index=False)
print(f"overdose_deaths.csv: {len(deaths):,} rows across {deaths['drug'].nunique()} drugs")

# --- population (tab-delimited) ---
pop_path = glob.glob("data/cdc_wonder/*population*.xls")[0]
pop = pd.read_csv(pop_path, sep="\t", dtype=str, engine="python", on_bad_lines="skip")
pop = pop[pop["Year Code"].astype(str).str.match(r"^\d{4}$", na=False)].copy()
pop["year"] = pop["Year Code"].str.strip().astype(int)
pop["population"] = pop["Population"].str.strip().astype(int)
pop[["year", "population"]].to_csv("staging/population.csv", index=False)
print(f"population.csv: {len(pop)} rows ({pop['year'].min()}-{pop['year'].max()})")
