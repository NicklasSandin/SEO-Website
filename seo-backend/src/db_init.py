"""Create the database from code and keep a schema version.

`init_db` is idempotent and is run at app start-up. To add a schema change later, append a
function to `MIGRATIONS` (the position in the list is the version it upgrades to) and raise
`SCHEMA_VERSION`. A database written by a newer version of the code is refused rather than guessed at.
"""
from __future__ import annotations

import logging

from .extensions import db
from .models import SchemaInfo

log = logging.getLogger(__name__)

# MIGRATIONS[i] upgrades a database from version i+1 to version i+2. Version 1 is the
# initial schema created by `db.create_all()`, so the list is empty for now.
MIGRATIONS: list = []
SCHEMA_VERSION = 1 + len(MIGRATIONS)


class SchemaError(RuntimeError):
    pass


def init_db() -> int:
    """Create missing tables, run pending migrations, return the schema version."""
    db.create_all()
    info = db.session.get(SchemaInfo, 1)
    if info is None:
        db.session.add(SchemaInfo(id=1, version=SCHEMA_VERSION))
        db.session.commit()
        return SCHEMA_VERSION
    if info.version > SCHEMA_VERSION:
        raise SchemaError(
            f"Database schema version {info.version} is newer than this code understands ({SCHEMA_VERSION})."
        )
    while info.version < SCHEMA_VERSION:
        MIGRATIONS[info.version - 1](db.session)
        info.version += 1
        db.session.commit()
        log.info("Migrated database to schema version %s", info.version)
    return info.version
