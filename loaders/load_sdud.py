"""
loaders/load_sdud.py - stage the SDUD prescription data for Postgres.

SDUD = CMS (Centers for Medicare and Medicaid Services) State Drug Utilization Data: every outpatient prescription paid for by state Medicaid programs, reported per drug (NDC) x state x quarter.

Loads the 8 yearly SDUD CSVs line by line, keeps only Oregon rows
(State == 'OR'), and writes one tidy file: staging/sdud_or.csv.

Why Python: glob picks up whatever yearly files are in data/sdud/, so the load
    is dynamic and reproducible. The stdlib csv module streams one row at a time
    (the national files are ~41M rows / 3.7 GB, too big to hold in pandas), is
    forgiving of malformed rows from other states, and correctly handles the
    quoted commas in some product names (e.g. "Creon 6,00").

Input:  data/sdud/*.csv - 8 national CMS State Drug Utilization Data files
        (2018-2025, ~41M rows). One row per drug package (NDC) x state x quarter
        x utilization type (FFSU fee-for-service / MCOU managed care).
        15 columns:
          - ids:    Utilization Type, State, NDC, Labeler Code, Product Code, Package Size
          - time:   Year, Quarter
          - drug:   Product Name (truncated to 10 chars, space-padded)
          - volume: Units Reimbursed (qty dispensed), Number of Prescriptions (fills)
          - money:  Total / Medicaid / Non Medicaid Amount Reimbursed
          - flag:   Suppression Used (true = counts < 11, numbers blanked)

Output: staging/sdud_or.csv - same 15 columns, Oregon rows only (~753k).
        ~54% of rows are suppressed (count < 11), with their numeric fields blank.

Notes:
  * Filtering to Oregon here means Postgres stores ~750k rows instead of ~41M,
    so the database stays small and fast.
  * Rows are copied as-is (no cleaning or type conversion); that happens in SQL.
  * Every yearly file must share the first file's header, or the columns would
    silently misalign in the combined output - checked below.

Usage (measure_110 env active):
    python loaders/load_sdud.py
"""

import csv
import glob
import os
from pathlib import Path

# --- Setup ---
# Run relative to the project root (this file lives in loaders/).
ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
Path("staging").mkdir(exist_ok=True)

IN_GLOB = "data/sdud/*.csv"
OUT_PATH = "staging/sdud_or.csv"
STATE_FILTER = "OR"

# --- Filter every yearly file to Oregon ---
source_files = sorted(glob.glob(IN_GLOB))  # identify and sort raw yearly CSV files
if not source_files:
    raise FileNotFoundError(f"no files match {IN_GLOB}")

kept = 0
first_header = None

with open(OUT_PATH, "w", newline="", encoding="utf-8") as fout:
    # initialize output CSV file
    writer = csv.writer(fout)

    for path in source_files:
        with open(path, newline="", encoding="utf-8") as fin:
            reader = csv.reader(fin)
            header = next(reader)  # just pull out the first row of column names
            state_idx = header.index("State")  # which column holds the state
            if first_header is None:
                first_header = header
                writer.writerow(header)  # write the header once for the output file
            elif header != first_header:
                raise ValueError(f"{os.path.basename(path)}: columns differ from the first file")
            # go through loaded yearly csv and filter for specific state's data
            for row in reader:
                if len(row) > state_idx and row[state_idx] == STATE_FILTER:  # skip blank lines and filter for specific state
                    writer.writerow(row)
                    kept += 1
        print(f"  processed {os.path.basename(path)} (Oregon rows so far: {kept:,})")

print(f"\nwrote {OUT_PATH}: {kept:,} Oregon rows")
