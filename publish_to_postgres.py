"""
publish_to_postgres.py - copy the analysis-ready mart tables from DuckDB into
PostgreSQL, so Tableau Desktop can connect to them live.

Prereqs:
  * the local Postgres server is running (see README "Postgres / Tableau")
  * build_db.py has been run so the mart tables exist in DuckDB

Usage (measure_110 env active):
    python publish_to_postgres.py
"""

import os
from pathlib import Path
import duckdb

ROOT = Path(__file__).resolve().parent
os.chdir(ROOT)

# Local dev Postgres connection (matches what you enter in Tableau).
PG = "dbname=measure110 user=postgres password=postgres host=localhost port=5432"

# Small, analysis-ready tables to publish for Tableau. Add more as we build them.
MARTS = ["mart_overdose_rate"]

# Writable connection: read_only would make the attached Postgres read-only too.
con = duckdb.connect("db/measure110.duckdb")
con.execute("INSTALL postgres; LOAD postgres;")
con.execute(f"ATTACH '{PG}' AS pg (TYPE postgres);")

for m in MARTS:
    con.execute(f"DROP TABLE IF EXISTS pg.{m};")
    con.execute(f"CREATE TABLE pg.{m} AS SELECT * FROM {m};")
    n = con.execute(f"SELECT COUNT(*) FROM pg.{m}").fetchone()[0]
    print(f"published {m}: {n} rows -> postgres")

con.close()
print("Done. Tableau -> PostgreSQL: localhost / 5432 / measure110 / postgres / postgres")
