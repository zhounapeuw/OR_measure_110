"""
loaders/load_cco.py - stage OHA CCO Metrics (Overall Population) for Postgres.

Reads the "CCO Metrics: Overall Population" workbook's tidy 'Data' sheet, cleans it,
and writes staging/cco_metrics_overall.csv: one row per metric x CCO x measurement
year (all metrics, 2011-2024). We filter to the SUD/IET measure in SQL.

Notes:
  * Header is on the 3rd row of the 'Data' sheet (header=2); row 0 is a title,
    row 1 a confidentiality note.
  * Denominators are reported ONLY at the 'CCO statewide' level (member
    confidentiality); per-CCO denominator cells are '-' -> NULL.
  * Service rate and benchmark are proportions (0-1); benchmark is stored as
    e.g. '48.6%' in the file and converted to 0.486 here.

Usage (measure_110 env active):
    python loaders/load_cco.py
"""

import glob
import os
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
Path("staging").mkdir(exist_ok=True)

f = glob.glob("data/CCO/*Overall Population*.xlsx")[0]
df = pd.read_excel(f, sheet_name="Data", header=2)
df.columns = [str(c).strip() for c in df.columns]


def num(series):
    """Parse '-'/blank/'%' cells to numbers ('48.6%' -> 48.6, '-' -> NaN)."""
    s = series.astype(str).str.replace("%", "", regex=False).str.strip()
    s = s.replace({"-": "", "nan": "", "": None})
    return pd.to_numeric(s, errors="coerce")


out = pd.DataFrame({
    "year":          pd.to_datetime(df["Measurement year"], errors="coerce").dt.year.astype("Int64"),
    "rate_type":     df["Rate type"].astype(str).str.strip(),
    "metric_abbrev": df["Metric abbrv."].astype(str).str.strip(),
    "metric_name":   df["Metric name"].astype(str).str.strip(),
    "cco":           df["CCO name"].astype(str).str.strip(),
    "service_rate":  num(df["Service rate"]),
    "denominator":   num(df["Denominator"]).astype("Int64"),
    "benchmark":     (num(df["Benchmark"]) / 100.0),   # '48.6%' -> 0.486
})
out = out[out["metric_name"].notna() & (out["metric_name"] != "nan") & out["year"].notna()]
out.to_csv("staging/cco_metrics_overall.csv", index=False)

print(f"wrote staging/cco_metrics_overall.csv: {len(out):,} rows | "
      f"{out['metric_abbrev'].nunique()} metrics | {out['cco'].nunique()} CCOs | "
      f"years {int(out['year'].min())}-{int(out['year'].max())}")

# --- County-level IET for choropleth maps (from the Geographic Disparities workbook) ---
# The per-county 'CCO statewide' row = the county total (all members, all CCOs), which is
# the one clean value per county. We take the latest year and pivot the two 18+ components
# into initiation/engagement columns. Tableau geocodes 'county' + 'state' natively.
gf = glob.glob("data/CCO/*Geographic Disparities*.xlsx")[0]
g = pd.read_excel(gf, sheet_name="Data", header=1)
g.columns = [str(c).strip() for c in g.columns]
g["year"] = pd.to_datetime(g["Measurement year"], errors="coerce").dt.year
g["rate"] = num(g["Service rate"])
latest = int(g["year"].max())
sel = g[(g["Breakout"] == "County") & (g["CCO name"] == "CCO statewide")
        & (g["year"] == latest) & g["Metric abbrv."].isin(["IET_INI_18", "IET_ENG_18"])]
county = (sel.pivot_table(index="Location", columns="Metric abbrv.", values="rate")
             .reset_index()
             .rename(columns={"Location": "county", "IET_INI_18": "initiation", "IET_ENG_18": "engagement"}))
county["state"] = "Oregon"
county = county[["county", "state", "initiation", "engagement"]]
county.to_csv("staging/cco_county_iet.csv", index=False)
print(f"wrote staging/cco_county_iet.csv: {county['initiation'].notna().sum()} counties "
      f"with data (year {latest})")
