"""
loaders/load_cdc.py - stage the CDC WONDER data for Postgres.

Reads the per-drug Oregon overdose-death exports and the Oregon population
export, drops their notes/caveats footers, and writes two tidy files.

Why Python: the WONDER exports are not clean tables - each has a notes footer,
    the "Deaths" column mixes numbers with the word "Suppressed", the drug is
    only identified by the filename, and the population ".xls" is really a
    tab-delimited text file. pandas handles that parsing in a few lines; the
    files are small, so memory is not a concern.

Input:  data/cdc_wonder/OR overdose deaths*.csv - 6 files, one per drug category
        (multiple cause of death, Oregon, monthly, 2018 through the latest
        provisional month). Columns: Notes, Year, Year Code, Month, Month Code
        ("2024/07"), Deaths (count or "Suppressed" for 1-9), Population / Crude
        Rate / 95% CI (all "Not Applicable" at the monthly level - not used).
        data/cdc_wonder/*population*.xls - tab-delimited, one row per year
        (2018-2024). Columns: Notes, Year, Year Code, Deaths (all causes),
        Population, Crude Rate + 95% CI. Only Year Code and Population are used.

Output: staging/overdose_deaths.csv - one row per drug-month (~612 rows):
          drug, year, month, is_suppressed, deaths_known (blank if suppressed)
        staging/population.csv - one row per year: year, population

Notes:
  * Suppressed months are flagged, not dropped, so the SQL can carry low/high
    bounds (1-9 deaths) later.
  * The drug label comes from the filename (see DRUG_BY_FILENAME); a file whose
    name matches none of them gets drug = "unknown".

Usage (measure_110 env active):
    python loaders/load_cdc.py
"""

import glob
import os
from pathlib import Path

import pandas as pd

# --- Setup ---
# Run relative to the project root (this file lives in loaders/).
ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
Path("staging").mkdir(exist_ok=True)

DEATHS_GLOB = "data/cdc_wonder/OR overdose deaths*.csv"
POP_GLOB = "data/cdc_wonder/*population*.xls"
DEATHS_OUT = "staging/overdose_deaths.csv"
POP_OUT = "staging/population.csv"

# Filename fragment -> drug label, checked in this order (first match wins).
DRUG_BY_FILENAME = [
    ("cocaine", "cocaine"),
    ("psychostim_meth", "methamphetamine"),
    ("heroin", "heroin"),
    ("methadone", "methadone"),
    ("other_opioids", "rx_opioids"),
    ("other_synth_narc", "synthetic_opioids_fentanyl"),
]


# --- Helpers ---
def find_one(pattern: str) -> str:
    """Return the single file matching `pattern`; fail loudly on zero or several."""
    matches = glob.glob(pattern)
    if len(matches) != 1:
        raise FileNotFoundError(f"expected exactly 1 file for {pattern!r}, found {len(matches)}: {matches}")
    return matches[0]


def drug_from_filename(name: str) -> str:
    """Map a WONDER export filename to its drug label (see DRUG_BY_FILENAME)."""
    n = name.lower()
    for fragment, drug in DRUG_BY_FILENAME:
        if fragment in n:
            return drug
    return "unknown"


# --- Overdose deaths (6 files -> one drug-month table) ---
death_files = sorted(glob.glob(DEATHS_GLOB))
if not death_files:
    raise FileNotFoundError(f"no files match {DEATHS_GLOB}")

parts = []
for path in death_files:
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
deaths.to_csv(DEATHS_OUT, index=False)
print(f"overdose_deaths.csv: {len(deaths):,} rows across {deaths['drug'].nunique()} drugs")

# --- Population (tab-delimited, one row per year) ---
pop = pd.read_csv(find_one(POP_GLOB), sep="\t", dtype=str, engine="python", on_bad_lines="skip")
# keep only real yearly data rows (drops footer rows)
pop = pop[pop["Year Code"].astype(str).str.match(r"^\d{4}$", na=False)].copy()
pop["year"] = pop["Year Code"].str.strip().astype(int)
pop["population"] = pop["Population"].str.strip().astype(int)
pop[["year", "population"]].to_csv(POP_OUT, index=False)
print(f"population.csv: {len(pop)} rows ({pop['year'].min()}-{pop['year'].max()})")
