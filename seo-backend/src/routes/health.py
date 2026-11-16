from __future__ import annotations

from flask import Blueprint, current_app, jsonify
from sqlalchemy import text

from ..config import APP_VERSION
from ..extensions import db

bp = Blueprint("health", __name__)


@bp.get("/health")
def health():
    """Liveness and mode. Reports which data/text sources are active; never any secret values."""
    provider = current_app.extensions["siktio_provider"]
    config = current_app.config
    try:
        db.session.execute(text("SELECT 1"))
        database = "ok"
    except Exception:
        current_app.logger.exception("Health check: database error")
        database = "error"
    use_ai = config["REPORT_GENERATOR"] == "openai" or (config["REPORT_GENERATOR"] == "auto" and bool(config["OPENAI_API_KEY"]))
    body = {
        "status": "ok" if database == "ok" else "degraded",
        "version": APP_VERSION,
        "database": database,
        "rank_provider": provider.name,
        "rank_data_is_sample": provider.is_sample,
        "report_generator": "openai" if use_ai else "template",
        "registration_open": config["ALLOW_REGISTRATION"],
    }
    return jsonify(body), 200 if database == "ok" else 503
