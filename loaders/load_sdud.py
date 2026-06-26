"""
loaders/load_sdud.py - stage the SDUD prescription data for Postgres.

Streams the 8 yearly SDUD CSVs line by line, keeps only Oregon rows
(State == 'OR'), and writes one tidy file: staging/sdud_or.csv.

Filtering to Oregon here means Postgres stores ~750k rows instead of ~6M,
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

source_files = sorted(glob.glob("data/sdud/*.csv"))
out_path = "staging/sdud_or.csv"
kept = 0

with open(out_path, "w", newline="", encoding="utf-8") as fout:
    writer = csv.writer(fout)
    header_written = False

    for path in source_files:
        with open(path, newline="", encoding="utf-8") as fin:
            reader = csv.reader(fin)
            header = next(reader)
            state_idx = header.index("State")     # which column holds the state
            if not header_written:
                writer.writerow(header)            # write the header once
                header_written = True
            for row in reader:
                if len(row) > state_idx and row[state_idx] == "OR":
                    writer.writerow(row)
                    kept += 1
        print(f"  processed {os.path.basename(path)} (Oregon rows so far: {kept:,})")

print(f"\nwrote {out_path}: {kept:,} Oregon rows")
