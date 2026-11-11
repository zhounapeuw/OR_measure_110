"""
loaders/load_sdud.py - stage the SDUD prescription data for Postgres.

Loads the 8 yearly SDUD CSVs line by line, keeps only Oregon rows
(State == 'OR'), and writes one tidy file: staging/sdud_or.csv.

Why: Python's glob can be dynamic and reproducible for different input files. Also Python is more forgiving for differently formatted raw excel files.

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

Filtering to Oregon here means Postgres stores ~750k rows instead of ~41M,
so the database stays small and fast. Uses the stdlib csv module, which
correctly handles the quoted commas in some product names (e.g. "Creon 6,00").

Usage (measure_110 env active):
    python loaders/load_sdud.py
"""

import csv
import glob
import os
from pathlib import Path

# Run relative to the project root (this file lives in loaders/).
ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
Path("staging").mkdir(exist_ok=True)

source_files = sorted(glob.glob("data/sdud/*.csv")) # identify and sort raw yearly CSV files
out_path = "staging/sdud_or.csv"
state_filter = 'OR'
kept = 0

with open(out_path, "w", newline="", encoding="utf-8") as fout:
    # initialize output CSV file
    writer = csv.writer(fout)
    header_written = False

    for path in source_files:
        with open(path, newline="", encoding="utf-8") as fin:
            reader = csv.reader(fin)
            header = next(reader) # just pull out the first row of column names
            state_idx = header.index("State")     # which column holds the state
            if not header_written:
                writer.writerow(header)            # write the header once for the output file
                header_written = True
            # go through loaded yearly csv and filter for specific state's data
            for row in reader:
                if len(row) > state_idx and row[state_idx] == state_filter: # skip blank lines and filter for specific state
                    writer.writerow(row)
                    kept += 1
        print(f"  processed {os.path.basename(path)} (Oregon rows so far: {kept:,})")

print(f"\nwrote {out_path}: {kept:,} Oregon rows")
