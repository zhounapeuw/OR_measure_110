"""
loaders/load_samhsa.py - stage SAMHSA N-SUMHSS treatment-facility data for Postgres.

Produces staging/samhsa_facilities_or.csv: one row per Oregon facility per year
(2021-2024, the N-SUMHSS years that carry substance-use medication data), with a
buprenorphine flag and the point-in-time buprenorphine client count.

Columns kept from the raw 966-column survey:
  LOCATIONSTATE  - facility state (filter to OR)
  OTXBUP         - facility uses buprenorphine: 1 yes / 0 no / L,M = not applicable
  HIBUPNUM/RCBUPNUM/OPBUPNUM - clients on buprenorphine by setting
                   (hospital-inpatient / residential / outpatient) on the census date

Output columns:
  year        - survey year
  offers_bup  - 1 / 0 / NULL (L,M -> NULL)
  bup_clients - total buprenorphine clients at that facility (sum of the 3 settings)

Note: 2019-2020 are N-MHSS (mental-health only) and lack these fields, so they are
excluded. Definitions should be confirmed against the SAMHSA codebook.

Usage (measure_110 env active):
    python loaders/load_samhsa.py
"""

import glob
import os
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
Path("staging").mkdir(exist_ok=True)

NUM_COLS = ["HIBUPNUM", "RCBUPNUM", "OPBUPNUM"]
parts = []

for year in (2021, 2022, 2023, 2024):
    path = glob.glob(f"data/SAMHSA/*{year}*/NSUMHSS_{year}_PUF_CSV.csv")[0]
    df = pd.read_csv(path, usecols=["LOCATIONSTATE", "OTXBUP"] + NUM_COLS, dtype=str)
    orr = df[df["LOCATIONSTATE"] == "OR"].copy()

    orr["year"] = year
    orr["offers_bup"] = orr["OTXBUP"].map({"1": 1, "0": 0})        # L,M -> NaN
    nums = orr[NUM_COLS].apply(pd.to_numeric, errors="coerce")     # L,M -> NaN
    orr["bup_clients"] = nums.clip(lower=0).sum(axis=1)            # negatives->0, NaN skipped

    parts.append(orr[["year", "offers_bup", "bup_clients"]])
    print(f"  {year}: {len(orr)} Oregon facilities")

out = pd.concat(parts, ignore_index=True)
out["offers_bup"] = out["offers_bup"].astype("Int64")
out["bup_clients"] = out["bup_clients"].astype("Int64")
out.to_csv("staging/samhsa_facilities_or.csv", index=False)
print(f"\nwrote staging/samhsa_facilities_or.csv: {len(out)} facility-year rows")
