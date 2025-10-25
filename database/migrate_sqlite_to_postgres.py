
#!/usr/bin/env python3
'''
Migrate a SQLite .db into Postgres using psycopg3 COPY.

Usage:
  export DATABASE_URL='postgresql://user:pass@host:port/db?sslmode=require'
  python migrate_sqlite_to_postgres.py path/to/file.db [schema]
'''
import os, sys, sqlite3, tempfile, csv, re
from typing import List, Tuple
from psycopg import connect
from psycopg.rows import dict_row

def ensure_sslmode(url: str) -> str:
    return url if "sslmode=" in url else (url + ("&" if "?" in url else "?") + "sslmode=require")

TYPE_MAP = [
    (re.compile("int", re.I),              "BIGINT"),
    (re.compile("char|clob|text", re.I),   "TEXT"),
    (re.compile("blob", re.I),             "BYTEA"),
    (re.compile("real|floa|doub", re.I),   "DOUBLE PRECISION"),
    (re.compile("bool", re.I),             "BOOLEAN"),
    (re.compile(r"timestamp|datetime", re.I), "TIMESTAMPTZ"),
    (re.compile(r"\bdate\b", re.I),        "DATE"),
    (re.compile("numeric|dec", re.I),      "NUMERIC"),
]

def map_type(sqlite_decl: str) -> str:
    if not sqlite_decl:
        return "TEXT"
    for rx, pg in TYPE_MAP:
        if rx.search(sqlite_decl):
            return pg
    return "TEXT"

def qident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'

def get_tables(c: sqlite3.Connection):
    cur = c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name;")
    return [r[0] for r in cur.fetchall()]

def get_table_info(c: sqlite3.Connection, table: str):
    cols = c.execute(f"PRAGMA table_info({qident(table)});").fetchall()
    columns = [(r[1], r[2], bool(r[3]), r[5]) for r in cols]  # name, decl, notnull, pk
    pks = [r[1] for r in cols if r[5]]
    return columns, pks

def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    sqlite_path = sys.argv[1]
    schema = sys.argv[2] if len(sys.argv) > 2 else "public"
    dburl = os.environ.get("DATABASE_URL") or os.environ.get("DATABASE_PUBLIC_URL")
    if not dburl:
        print("Set DATABASE_URL or DATABASE_PUBLIC_URL", file=sys.stderr); sys.exit(2)
    dburl = ensure_sslmode(dburl)

    sc = sqlite3.connect(sqlite_path)
    sc.row_factory = sqlite3.Row
    tables = get_tables(sc)
    if not tables:
        print("No tables found", file=sys.stderr); sys.exit(1)

    with connect(dburl, row_factory=dict_row) as pc:
        pc.execute(f'CREATE SCHEMA IF NOT EXISTS {qident(schema)};'); pc.commit()

        for t in tables:
            cols, pks = get_table_info(sc, t)
            col_defs = [f"{qident(n)} {map_type(d)}{' NOT NULL' if nn else ''}" for n,d,nn,pkf in cols]
            pk_sql = f", PRIMARY KEY ({', '.join(qident(n) for n in pks)})" if pks else ""
            create_sql = f'CREATE TABLE IF NOT EXISTS {qident(schema)}.{qident(t)} ({", ".join(col_defs)}{pk_sql});'
            pc.execute(create_sql); pc.commit()

            # Export to temp CSV
            col_names = [c[0] for c in cols]
            tmp_path = tempfile.mktemp(suffix=".csv")
            with open(tmp_path, "w", newline="") as f:
                w = csv.writer(f); w.writerow(col_names)
                for row in sc.execute(f"SELECT * FROM {qident(t)};"):
                    w.writerow([row[c] for c in col_names])

            pc.execute(f'TRUNCATE TABLE {qident(schema)}.{qident(t)};')
            copy_sql = f'COPY {qident(schema)}.{qident(t)} ({", ".join(qident(c) for c in col_names)}) FROM STDIN WITH (FORMAT csv, HEADER true)'
            with pc.cursor() as cur, open(tmp_path, "rb") as f:
                with cur.copy(copy_sql) as copy:
                    while True:
                        chunk = f.read(1024 * 1024)
                        if not chunk: break
                        copy.write(chunk)
            pc.commit()
            os.remove(tmp_path)
            print(f"Loaded {t} into {schema}.{t}")

    print("Done.")

if __name__ == "__main__":
    main()
