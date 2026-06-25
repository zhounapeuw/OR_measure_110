"""
build_db.py - set up the project's DuckDB database.

It connects to db/measure110.duckdb (creating it if needed) and runs every
.sql file in the sql/ folder in order (01_, 02_, ...). Re-run it any time you
add or change a .sql file.

Usage (from this project folder, with the measure_110 env active):
    python build_db.py
"""

import os
from pathlib import Path
import duckdb

# Always work relative to this project folder, so the file paths inside the
# .sql files (like 'sdud/*.csv') resolve no matter where you run this from.
ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)

con = duckdb.connect("db/measure110.duckdb")

# Run each SQL file in filename order.
for sql_file in sorted(Path("sql").glob("*.sql")):
    print(f"running {sql_file.name} ...")
    con.execute(sql_file.read_text())

# Quick sanity checks.
oregon_rows = con.execute(
    "SELECT COUNT(*) FROM raw_sdud WHERE \"State\" = 'OR'"
).fetchone()[0]
print(f"OK - raw_sdud sees {oregon_rows:,} Oregon rows")

rate_rows = con.execute("SELECT COUNT(*) FROM mart_overdose_rate").fetchone()[0]
print(f"OK - mart_overdose_rate has {rate_rows} drug-year rows")

con.close()
