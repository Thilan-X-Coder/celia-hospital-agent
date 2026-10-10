"""
One place to open database connections.
Every tool will use:   with get_conn() as conn: ...
"""
import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "celia.db"


@contextmanager
def get_conn():
    """Open a connection, commit if all is OK, roll back on error, always close."""
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}. Run: python -m db.seed")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row            # rows behave like dicts: row["full_name"]
    conn.execute("PRAGMA foreign_keys = ON")  # must be turned on for EVERY connection
    try:
        yield conn                             # your code runs here
        conn.commit()                          # success -> save
    except Exception:
        conn.rollback()                        # any error -> undo everything
        raise
    finally:
        conn.close()                           # always close the file