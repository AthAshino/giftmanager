"""Standalone JSON → SQLite data migration.

Run before starting the app (the container entrypoint does this automatically):

    python migrate.py [data-dir]

Default data dir is ./data. Idempotent: legacy JSON files (users.json,
ideas.json, settings.json) are only imported into giftmanager.db when the
corresponding table is empty, so it is safe to run on every boot.
"""

import sys
from pathlib import Path

import storage


def main():
    data_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("./data")
    storage.initialize(data_dir)
    db = data_dir / storage.DB_FILENAME
    print(f"[migrate] SQLite storage ready at {db}")


if __name__ == "__main__":
    main()
