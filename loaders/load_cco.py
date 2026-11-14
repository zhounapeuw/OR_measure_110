"""
loaders/load_cco.py - stage OHA CCO Metrics for Postgres.

Reads two Oregon Health Authority CCO Metrics workbooks: the statewide/per-CCO
metrics (all metrics, all years) and the county-level IET rates used for the
Tableau choropleth maps.

Why Python: the inputs are Excel workbooks with title rows above the header,
    several sheets, percent strings ("48.6%") and "-" placeholders in numeric
    columns, and the county IET needs a pivot. pandas reads and reshapes them in
    a few lines; the files are small, so memory is not a concern.

Input:  data/CCO/*Overall Population*.xlsx, sheet 'Data' (~9.6k rows). One row per
        metric x CCO x measurement year (85 metrics, 16 CCOs + 'CCO statewide',
        2011-2024). Columns used: Measurement year, Rate type, Metric abbrv.,
        Metric name, CCO name, Service rate, Denominator, Benchmark. (Also has
        change-from-prior-year, improvement target and data-warning columns.)
        data/CCO/*Geographic Disparities*.xlsx, sheet 'Data' (~84k rows). Same
        metric x CCO x year rows broken out by geography: Breakout (County /
        Primary Care Service Area / Frontier, Rural, Urban) + Location.

Output: staging/cco_metrics_overall.csv - one row per metric x CCO x year:
          year, rate_type, metric_abbrev, metric_name, cco,
          service_rate (0-1), denominator (statewide only), benchmark (0-1)
        staging/cco_county_iet.csv - one row per Oregon county, latest year:
          county, state, initiation, engagement (IET ages 18+, proportions 0-1)

Notes:
  * Overall workbook: header is on the 3rd row of 'Data' (header=2); row 0 is a
    title, row 1 a confidentiality note. Geographic workbook: header on row 2.
  * Denominators are reported ONLY at the 'CCO statewide' level (member
    confidentiality); per-CCO denominator cells are '-' -> NULL.
  * Benchmark is stored as e.g. '48.6%' in the file and converted to 0.486 here.
  * All metrics are kept; the SUD/IET measure is selected in SQL.

Usage (measure_110 env active):
    python loaders/load_cco.py
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

# define input/output files; info on input files in comment header
OVERALL_GLOB = "data/CCO/*Overall Population*.xlsx"
GEO_GLOB = "data/CCO/*Geographic Disparities*.xlsx"
OVERALL_OUT = "staging/cco_metrics_overall.csv"
COUNTY_OUT = "staging/cco_county_iet.csv"

+# The workbooks are LONG format: every metric shares the same columns, and the
+# "Metric abbrv." column says which metric a row is (85 codes in total). These
+# two codes mark the rows we want:
+#   IET_INI_18 (AKA Initiation): adults 18+: % of new SUD diagnoses that got
+#                treatment within 14 days of the diagnosis
+#   IET_ENG_18 (Engagement): adults 18+: % of new SUD diagnoses followed by 2+
+#                more visits/medication treatments within 34 days of starting
IET_METRICS = {"IET_INI_18": "initiation", "IET_ENG_18": "engagement"}


# --- Helpers ---
def find_one(pattern: str) -> str:
    """Return the single file matching `pattern`; fail loudly on zero or several."""
    matches = glob.glob(pattern)
    if len(matches) != 1:
        raise FileNotFoundError(f"expected exactly 1 file for {pattern!r}, found {len(matches)}: {matches}")
    return matches[0]


def num(series: pd.Series) -> pd.Series:
    """Convert a column of messy Excel cells to numbers.

    Handles the three kinds of cell found in the CCO workbooks:
      - a number:           0.417   -> 0.417
      - a percent string:  "48.6%"  -> 48.6   (% sign removed; NOT divided by 100)
      - a dash or empty:     "-"    -> NaN    (OHA's placeholder for "no value")
    """
    s = series.astype(str).str.replace("%", "", regex=False).str.strip()
    s = s.replace({"-": "", "nan": "", "": None})
    return pd.to_numeric(s, errors="coerce")


# --- Overall population: every metric x CCO x year ---
# header=2: the column names are on the 3rd row (0-indexed). Rows 0-1 are a
# title and a confidentiality note that pandas should skip.
overall = pd.read_excel(find_one(OVERALL_GLOB), sheet_name="Data", header=2)
# Excel headers often have trailing spaces ("CCO name "), which would make
# overall["CCO name"] fail with a KeyError. Strip them all once here.
overall.columns = [str(c).strip() for c in overall.columns]

# build the output dataframe 
out = pd.DataFrame({
    "year":          pd.to_datetime(overall["Measurement year"], errors="coerce").dt.year.astype("Int64"),
    "rate_type":     overall["Rate type"].astype(str).str.strip(),
    "metric_abbrev": overall["Metric abbrv."].astype(str).str.strip(),
    "metric_name":   overall["Metric name"].astype(str).str.strip(),
    "cco":           overall["CCO name"].astype(str).str.strip(),
    "service_rate":  num(overall["Service rate"]),
    "denominator":   num(overall["Denominator"]).astype("Int64"),
    "benchmark":     (num(overall["Benchmark"]) / 100.0),   # '48.6%' -> 0.486
})
# drop non-data rows (no metric name or year); astype(str) turned NaN into "nan"
out = out[out["metric_name"].notna() & (out["metric_name"] != "nan") & out["year"].notna()]
out.to_csv(OVERALL_OUT, index=False)

print(f"wrote {OVERALL_OUT}: {len(out):,} rows | "
      f"{out['metric_abbrev'].nunique()} metrics | {out['cco'].nunique()} CCOs | "
      f"years {int(out['year'].min())}-{int(out['year'].max())}")

# --- County-level IET for choropleth maps (Geographic Disparities workbook) ---
# The per-county 'CCO statewide' row = the county total (all members, all CCOs), which is
# the one clean value per county. We take the latest year and pivot the two 18+ components
# into initiation/engagement columns. Tableau geocodes 'county' + 'state' natively.
geo = pd.read_excel(find_one(GEO_GLOB), sheet_name="Data", header=1)
geo.columns = [str(c).strip() for c in geo.columns]
geo["year"] = pd.to_datetime(geo["Measurement year"], errors="coerce").dt.year
geo["rate"] = num(geo["Service rate"])
latest = int(geo["year"].max())

# note: select only "CCO statewide" 
county_rows = geo[(geo["Breakout"] == "County") & (geo["CCO name"] == "CCO statewide")
                  & (geo["year"] == latest) & geo["Metric abbrv."].isin(list(IET_METRICS))]
# Long -> wide. Right now there are 2 rows per county (one per metric). The
# pivot makes 1 row per county with a column for each metric:
#     Location | IET_ENG_18 | IET_INI_18
# the rename replaces the IET column names to be more interpretable
county = (county_rows.pivot_table(index="Location", columns="Metric abbrv.", values="rate")
                     .reset_index()
                     .rename(columns={"Location": "county", **IET_METRICS}))
county["state"] = "Oregon"
county = county[["county", "state", "initiation", "engagement"]] # reorder columns to line up with postgres table columns
county.to_csv(COUNTY_OUT, index=False)
print(f"wrote {COUNTY_OUT}: {county['initiation'].notna().sum()} counties "
      f"with data (year {latest})")
