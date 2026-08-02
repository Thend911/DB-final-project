"""
init_db.py
Requirement 4: Database Implementation.

Reads ecommerce_schema.sql (schema creation + INSERT statements) and
executes it against a fresh SQLite database file: ecommerce.db

Usage:
    python3 init_db.py
    python3 init_db.py --schema path/to/schema.sql --db path/to/output.db
"""

import argparse
import sqlite3
import sys
from pathlib import Path


def init_database(schema_path: Path, db_path: Path) -> None:
    if not schema_path.exists():
        print(f"Error: schema file not found: {schema_path}")
        sys.exit(1)

    sql_script = schema_path.read_text(encoding="utf-8")

    # Start fresh each time so the script is safely re-runnable
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.executescript(sql_script)
        conn.commit()

        # Quick sanity check / summary
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = [row[0] for row in cur.fetchall()]

        print(f"Database created at: {db_path.resolve()}")
        print(f"Tables created ({len(tables)}): {', '.join(tables)}")

        for table in tables:
            cur.execute(f'SELECT COUNT(*) FROM "{table}";')
            count = cur.fetchone()[0]
            print(f"  - {table}: {count} row(s)")

    except sqlite3.Error as e:
        print(f"SQLite error while initializing database: {e}")
        sys.exit(1)
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Initialize the e-commerce SQLite database.")
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path(__file__).parent / "ecommerce_schema.sql",
        help="Path to the .sql schema/data file (default: ecommerce_schema.sql)",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=Path(__file__).parent / "ecommerce.db",
        help="Path for the output SQLite database file (default: ecommerce.db)",
    )
    args = parser.parse_args()
    init_database(args.schema, args.db)


if __name__ == "__main__":
    main()