"""SQLite-backed storage for giftmanager.

Replaces the legacy JSON files (users.json, ideas.json, settings.json) with a
single SQLite database (giftmanager.db). The public API keeps the exact same
data shapes as the old JSON helpers — callers pass the data directory and get
back lists of dicts — so the rest of the application is unaffected.

Migration: initialize() is idempotent and transparently imports any existing
JSON files into the SQLite database on first boot, so upgrading an existing
deployment requires no user action.
"""

import json
import sqlite3
from pathlib import Path

DB_FILENAME = "giftmanager.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS gift_ideas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

# Demo gift idea seeded on a truly fresh install (mirrors the old ideas.json default)
_DEMO_IDEAS = [
    {
        "user_id": "demo",
        "gift_idea_id": 1,
        "gift_name": "Default",
        "description": "dont delete",
        "link": "icbest.ca",
        "added_by": "demo",
        "bought_by": "",
    }
]


def db_path(data_dir):
    return Path(data_dir) / DB_FILENAME


def _connect(data_dir):
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path(data_dir)))
    conn.row_factory = sqlite3.Row
    return conn


def _init_schema(conn):
    conn.executescript(_SCHEMA)


def _table_empty(conn, table):
    row = conn.execute(f"SELECT COUNT(*) AS n FROM {table}").fetchone()
    return row["n"] == 0


def _import_json_list(conn, json_path, table):
    """Import a JSON list-of-dicts file into one row per item, preserving order.

    Returns True if the file was successfully imported (and may be removed).
    """
    try:
        items = json.loads(json_path.read_text())
    except (json.JSONDecodeError, OSError):
        return False
    if not isinstance(items, list):
        return False
    conn.executemany(
        f"INSERT INTO {table} (data) VALUES (?)",
        [(json.dumps(item, ensure_ascii=False),) for item in items],
    )
    return True


def _import_json_map(conn, json_path, table):
    """Import a JSON dict file into one key/value row per entry.

    Returns True if the file was successfully imported (and may be removed).
    """
    try:
        items = json.loads(json_path.read_text())
    except (json.JSONDecodeError, OSError):
        return False
    if not isinstance(items, dict):
        return False
    conn.executemany(
        f"INSERT INTO {table} (key, value) VALUES (?, ?)",
        [(str(key), json.dumps(value, ensure_ascii=False)) for key, value in items.items()],
    )
    return True


def initialize(data_dir):
    """Idempotent bootstrap: create schema, migrate JSON → SQLite, seed demo.

    Safe to call on every boot and from the container entrypoint. Migrated
    legacy JSON files are deleted once their data has been committed to SQLite.
    """
    data_dir = Path(data_dir)
    had_ideas_json = (data_dir / "ideas.json").exists()

    migrated = []

    with _connect(data_dir) as conn:
        _init_schema(conn)

        if _table_empty(conn, "gift_ideas"):
            if _import_json_list(conn, data_dir / "ideas.json", "gift_ideas"):
                migrated.append(data_dir / "ideas.json")
        if _table_empty(conn, "users"):
            if _import_json_list(conn, data_dir / "users.json", "users"):
                migrated.append(data_dir / "users.json")
        if _table_empty(conn, "settings"):
            if _import_json_map(conn, data_dir / "settings.json", "settings"):
                migrated.append(data_dir / "settings.json")

        # Fresh install with no legacy data: seed the demo idea.
        if not had_ideas_json and _table_empty(conn, "gift_ideas"):
            conn.executemany(
                "INSERT INTO gift_ideas (data) VALUES (?)",
                [(json.dumps(idea, ensure_ascii=False),) for idea in _DEMO_IDEAS],
            )

        conn.commit()

    for path in migrated:
        path.unlink(missing_ok=True)
        print(f"[storage] Migrated and removed {path}")


def load_gift_ideas(data_dir):
    initialize(data_dir)
    with _connect(data_dir) as conn:
        rows = conn.execute("SELECT data FROM gift_ideas ORDER BY id").fetchall()
    return [json.loads(row["data"]) for row in rows]


def save_gift_ideas(data_dir, gift_ideas):
    initialize(data_dir)
    with _connect(data_dir) as conn:
        conn.execute("DELETE FROM gift_ideas")
        conn.executemany(
            "INSERT INTO gift_ideas (data) VALUES (?)",
            [(json.dumps(idea, ensure_ascii=False),) for idea in gift_ideas],
        )
        conn.commit()


def load_users(data_dir):
    initialize(data_dir)
    with _connect(data_dir) as conn:
        rows = conn.execute("SELECT data FROM users ORDER BY id").fetchall()
    return [json.loads(row["data"]) for row in rows]


def save_users(data_dir, users):
    initialize(data_dir)
    with _connect(data_dir) as conn:
        conn.execute("DELETE FROM users")
        conn.executemany(
            "INSERT INTO users (data) VALUES (?)",
            [(json.dumps(user, ensure_ascii=False),) for user in users],
        )
        conn.commit()


def load_settings(data_dir):
    initialize(data_dir)
    with _connect(data_dir) as conn:
        rows = conn.execute("SELECT key, value FROM settings").fetchall()
    return {row["key"]: json.loads(row["value"]) for row in rows}


def save_settings(data_dir, settings):
    initialize(data_dir)
    with _connect(data_dir) as conn:
        conn.execute("DELETE FROM settings")
        conn.executemany(
            "INSERT INTO settings (key, value) VALUES (?, ?)",
            [(str(key), json.dumps(value, ensure_ascii=False)) for key, value in settings.items()],
        )
        conn.commit()
