#!/bin/sh
set -e

# Migrate any legacy JSON data (users.json / ideas.json / settings.json) into
# SQLite before the app starts. Idempotent and transparent — no user action
# required when upgrading an existing deployment.
DATA_DIR="${DATA_DIR:-/app/data}"
echo "[entrypoint] Migrating JSON data → SQLite (if needed) in ${DATA_DIR}..."
python migrate.py "${DATA_DIR}"

exec "$@"
