#!/usr/bin/env python3

import hashlib
import os
import re
import sys

MIGRATION_REGEX = re.compile(r"^([0-9]{3}_[A-Za-z0-9_-]+)\.sql$")
CORE_MIGRATIONS_DIR = "migrations"
GAMES_DIR = "static/games"

if not os.path.isdir(CORE_MIGRATIONS_DIR) or not os.path.isdir(GAMES_DIR):
    print("ERROR: This script should be run from the repo top level")
    sys.exit(1)

# Work either as `python3 -m scripts.migrate` or `python3 scripts/migrate.py`
ROOT = os.path.abspath(f"{os.path.dirname(os.path.abspath(__file__))}/..")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from imports import db
from imports.games import GAME_LIST


def ensure_schema_migrations_table(conn):
    """
    Create schema migrations table if it hasn't already been created

    This table is created on install to track what has/has not been applied
      to the local install database
    With this table, database schema changes can be implemented smoothly both
      for the top-level install and for each game using its own db functions
    """

    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS schema_migrations (
              namespace TEXT NOT NULL,
              title TEXT NOT NULL,
              checksum TEXT,
              applied_at TIMESTAMPTZ NOT NULL DEFAULT now(),
              PRIMARY KEY (namespace, title)
            )
            """
        )


def get_applied_migration(conn, namespace, title):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT checksum
            FROM schema_migrations
            WHERE namespace = %(namespace)s
              AND title = %(title)s
            """,
            {
                "namespace": namespace,
                "title": title
            }
        )

        return cur.fetchone()


def record_migration(conn, namespace, title, checksum):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO schema_migrations (
              namespace,
              title,
              checksum
            )
            VALUES (
              %(namespace)s,
              %(title)s,
              %(checksum)s
            )
            """,
            {
                "namespace": namespace,
                "title": title,
                "checksum": checksum
            }
        )


def migration_files(directory):
    if not os.path.isdir(directory):
        return []

    files = []
    for name in os.listdir(directory):
        path = f"{directory}/{name}"
        if not os.path.isfile(path) or not MIGRATION_REGEX.match(name):
            print(f"WARNING: Skipping {path!r}")
            continue
        files.append(path)

    return sorted(files)


def apply_migration_file(conn, namespace, path):
    match = MIGRATION_REGEX.match(os.path.basename(path))
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()

    title = match.group(1)
    checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()
    applied = get_applied_migration(conn, namespace, title)

    if applied:
        old_checksum = applied["checksum"]
        if old_checksum and old_checksum != checksum:
            raise RuntimeError(f"Migration checksum mismatch for {namespace}/{title}: {path!r}")

        print(f"skip  {namespace}/{title}")
        return False

    print(f"apply {namespace}/{title}")
    with conn.cursor() as cur:
        cur.execute(sql)

    record_migration(conn, namespace, title, checksum)
    return True


def apply_migration_dir(conn, namespace, directory):
    applied_count = 0

    for migration in migration_files(directory):
        if apply_migration_file(conn, namespace, migration):
            applied_count += 1

    return applied_count


def apply_game_migrations(conn):
    applied_count = 0

    for game in GAME_LIST:
        if not game.has_migrations:
            continue

        migrations_dir = f"{GAMES_DIR}/{game.source_name}/migrations"
        applied_count += apply_migration_dir(conn, f"game:{game.source_name}", migrations_dir)

    return applied_count


def migrate():
    """
    Function to apply db schema migration files based on current state of db
      at update/install time

    Migration files are searched for in:
      migrations/MIGRATION_REGEX (core)
      static/games/{game}/migrations/MIGRATION_REGEX (per-game)

    Game migrations are applied when {game}.json has "db_migrations": true
    """

    with db.db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT pg_advisory_xact_lock(940940)")

        ensure_schema_migrations_table(conn)

        core_count = apply_migration_dir(conn, "core", CORE_MIGRATIONS_DIR)
        game_count = apply_game_migrations(conn)

        print(f"INFO: Applied {core_count} core migration(s)")
        print(f"INFO: Applied {game_count} game migration(s)")


if __name__ == "__main__":
    migrate()

