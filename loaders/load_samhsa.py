"""
loaders/load_samhsa.py - stage SAMHSA N-SUMHSS treatment-facility data for Postgres.

Reads the national N-SUMHSS facility survey for each year that carries
substance-use medication data, keeps Oregon facilities, and writes one row per
facility per year with a buprenorphine flag and client count.

Why Python: each yearly survey file is a 966-column national CSV, but only 5
    columns and one state are needed. pandas reads just those columns
    (usecols), and the survey's missing-value codes (L, M, negatives) need
    mapping to NULL before anything reaches SQL.

Input:  data/SAMHSA/*<year>*/NSUMHSS_<year>_PUF_CSV.csv - one national public-use
        file per year, 2021-2024; one row per treatment facility, 966 columns.
        Columns used:
          LOCATIONSTATE - facility state (filter to OR)
          OTXBUP        - facility uses buprenorphine: 1 yes / 0 no / L,M = not applicable
          HIBUPNUM/RCBUPNUM/OPBUPNUM - clients on buprenorphine by setting
                          (hospital-inpatient / residential / outpatient) on the census date

Output: staging/samhsa_facilities_or.csv - one row per Oregon facility per year
        (~1.8k rows):
          year        - survey year
          offers_bup  - 1 / 0 / NULL (L,M -> NULL)
          bup_clients - total buprenorphine clients at that facility (sum of the 3 settings)

Notes:
  * 2019-2020 are N-MHSS (mental-health only) and lack these fields, so they are
    excluded. Definitions should be confirmed against the SAMHSA codebook.
  * Not yet loaded into Postgres - no SQL file reads this output.
  * Known issue (left as-is for now): a facility whose three counts are all
    missing gets bup_clients = 0, not NULL, because sum() skips NaN; and
    clip(lower=0) turns negative missing-value codes into 0. Fix before use:
    mask negatives as NaN and use .sum(axis=1, min_count=1).

Usage (measure_110 env active):
    python loaders/load_samhsa.py
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

YEARS = (2021, 2022, 2023, 2024)
IN_PATTERN = "data/SAMHSA/*{year}*/NSUMHSS_{year}_PUF_CSV.csv"
OUT_PATH = "staging/samhsa_facilities_or.csv"
STATE_FILTER = "OR"
NUM_COLS = ["HIBUPNUM", "RCBUPNUM", "OPBUPNUM"]


# --- Helpers ---
def find_one(pattern: str) -> str:
    """Return the single file matching `pattern`; fail loudly on zero or several."""
    matches = glob.glob(pattern)
    if len(matches) != 1:
        raise FileNotFoundError(f"expected exactly 1 file for {pattern!r}, found {len(matches)}: {matches}")
    return matches[0]


# --- Filter each yearly survey to Oregon facilities ---
parts = []
for year in YEARS:
    path = find_one(IN_PATTERN.format(year=year))
    df = pd.read_csv(path, usecols=["LOCATIONSTATE", "OTXBUP"] + NUM_COLS, dtype=str)
    oregon = df[df["LOCATIONSTATE"] == STATE_FILTER].copy()

    oregon["year"] = year
    oregon["offers_bup"] = oregon["OTXBUP"].map({"1": 1, "0": 0})        # L,M -> NaN
    nums = oregon[NUM_COLS].apply(pd.to_numeric, errors="coerce")         # L,M -> NaN
    oregon["bup_clients"] = nums.clip(lower=0).sum(axis=1)                # negatives->0, NaN skipped

    parts.append(oregon[["year", "offers_bup", "bup_clients"]])
    print(f"  {year}: {len(oregon)} Oregon facilities")

out = pd.concat(parts, ignore_index=True)
out["offers_bup"] = out["offers_bup"].astype("Int64")
out["bup_clients"] = out["bup_clients"].astype("Int64")
out.to_csv(OUT_PATH, index=False)
print(f"\nwrote {OUT_PATH}: {len(out)} facility-year rows")
