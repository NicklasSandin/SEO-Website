import pytest
from flask import Flask

from src.db_init import SCHEMA_VERSION, SchemaError, init_db
from src.extensions import db
from src.models import SchemaInfo


def test_init_db_is_idempotent_and_records_the_version(app):
    with app.app_context():
        assert init_db() == SCHEMA_VERSION
        assert init_db() == SCHEMA_VERSION
        assert SchemaInfo.query.count() == 1


def test_a_database_from_newer_code_is_refused(app):
    with app.app_context():
        db.session.get(SchemaInfo, 1).version = SCHEMA_VERSION + 1
        db.session.commit()
        with pytest.raises(SchemaError):
            init_db()


def test_database_file_is_created_by_code(tmp_path):
    from src.app import create_app

    from .conftest import make_env

    path = tmp_path / "data" / "siktio.db"
    path.parent.mkdir()
    create_app(make_env(DATABASE_URL=f"sqlite:///{path}"))
    assert path.exists() and path.stat().st_size > 0
