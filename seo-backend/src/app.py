"""Application factory.

    gunicorn "src.app:create_app()"        (production)
    python -m src.main                      (local development)

`create_app()` reads the process environment. `create_app({...})` reads only the mapping you pass
(same variable names), which is what the tests do so a developer's real keys can never leak in.
"""
from __future__ import annotations

import logging
import os
from datetime import timedelta
from typing import Callable, Mapping

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from sqlalchemy import event
from sqlalchemy.engine import Engine
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import ConfigError, load_config
from .db_init import init_db
from .extensions import db
from .providers import RankProvider, build_provider
from .routes import register_routes
from .security import LoginThrottle
from .validation import ValidationError

CLIENT_HEADER = "X-Requested-With"
CLIENT_HEADER_VALUE = "siktio-web"
MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
    "font-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
)


@event.listens_for(Engine, "connect")
def _sqlite_foreign_keys(dbapi_connection, _record):
    # SQLite ignores foreign keys unless asked; other databases enforce them already.
    if dbapi_connection.__class__.__module__.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


def _default_static_dir() -> str | None:
    backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    for candidate in (
        os.path.join(os.path.dirname(backend_root), "seo-service-website", "dist"),
        os.path.join(backend_root, "static"),
    ):
        if os.path.isfile(os.path.join(candidate, "index.html")):
            return candidate
    return None


def create_app(
    env: Mapping[str, str] | None = None,
    *,
    provider: RankProvider | None = None,
    llm: Callable[..., str] | None = None,
) -> Flask:
    config = load_config(os.environ if env is None else env)

    app = Flask(__name__, instance_relative_config=True)
    database_url = config["DATABASE_URL"]
    if not database_url:
        os.makedirs(app.instance_path, exist_ok=True)
        database_url = f"sqlite:///{os.path.join(app.instance_path, 'siktio.db')}"
    app.config.update(config)
    app.config.update(
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MAX_CONTENT_LENGTH=64 * 1024,
        SESSION_COOKIE_NAME="siktio_session",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=config["SESSION_COOKIE_SECURE"],
        PERMANENT_SESSION_LIFETIME=timedelta(hours=config["SESSION_LIFETIME_HOURS"]),
        TESTING=config["APP_ENV"] == "testing",
    )
    if config["APP_ENV"] != "testing":
        logging.basicConfig(level=logging.INFO)

    if config["TRUST_PROXY_HEADERS"]:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)  # type: ignore[method-assign]

    if config["CORS_ORIGINS"]:
        CORS(
            app,
            resources={r"/api/*": {"origins": list(config["CORS_ORIGINS"])}},
            supports_credentials=True,
            allow_headers=["Content-Type", CLIENT_HEADER],
        )

    db.init_app(app)
    with app.app_context():
        init_db()

    app.extensions["siktio_provider"] = provider or build_provider(config)
    app.extensions["siktio_llm"] = llm
    app.extensions["siktio_login_throttle"] = LoginThrottle(
        config["LOGIN_MAX_FAILURES"], config["LOGIN_FAILURE_WINDOW_SECONDS"]
    )
    # Each registration costs a memory-hard password hash, so sign-ups per address are limited too.
    app.extensions["siktio_register_throttle"] = LoginThrottle(config["REGISTER_MAX_PER_HOUR"], 3600)
    if app.extensions["siktio_provider"].is_sample:
        app.logger.warning("Rank data comes from the SAMPLE provider: all results are invented fixture data.")

    register_routes(app)
    _register_hooks(app)
    _register_static(app, config["STATIC_DIR"] or _default_static_dir())
    return app


def _register_hooks(app: Flask) -> None:
    @app.before_request
    def require_client_header():
        # A custom header cannot be added cross-site without a CORS preflight, which the CORS
        # allow-list refuses; together with SameSite=Lax cookies this blocks CSRF.
        if request.method in MUTATING_METHODS and request.path.startswith("/api/"):
            if request.headers.get(CLIENT_HEADER) != CLIENT_HEADER_VALUE:
                return jsonify({"error": "Missing client header.", "code": "csrf"}), 403
        return None

    @app.after_request
    def security_headers(response):
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "no-referrer")
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        else:
            response.headers.setdefault("Content-Security-Policy", CSP)
        return response

    @app.errorhandler(ValidationError)
    def handle_validation(exc: ValidationError):
        return jsonify({"error": str(exc), "code": "validation_error", "field": exc.field}), 400

    @app.errorhandler(HTTPException)
    def handle_http(exc: HTTPException):
        if request.path.startswith("/api/"):
            return jsonify({"error": exc.description, "code": (exc.name or "error").lower().replace(" ", "_")}), exc.code
        return exc

    @app.errorhandler(Exception)
    def handle_unexpected(exc: Exception):
        # Log the traceback server-side; never put exception text in the response.
        app.logger.exception("Unhandled error on %s %s", request.method, request.path)
        return jsonify({"error": "Internal server error.", "code": "internal_error"}), 500

    @app.teardown_appcontext
    def remove_session(_exc):
        db.session.remove()


def _register_static(app: Flask, static_dir: str | None) -> None:
    @app.get("/", defaults={"path": ""})
    @app.get("/<path:path>")
    def serve_frontend(path: str):
        if path.startswith("api/") or path == "api":
            return jsonify({"error": "Not found.", "code": "not_found"}), 404
        if not static_dir or not os.path.isfile(os.path.join(static_dir, "index.html")):
            return (
                "Siktio API is running. The web interface has not been built: run `npm run build` in "
                "seo-service-website (see README).",
                200,
                {"Content-Type": "text/plain; charset=utf-8"},
            )
        if path:
            candidate = os.path.normpath(os.path.join(static_dir, path))
            if candidate.startswith(os.path.abspath(static_dir) + os.sep) and os.path.isfile(candidate):
                return send_from_directory(static_dir, path)
        response = send_from_directory(static_dir, "index.html")
        response.headers["Cache-Control"] = "no-cache"
        return response


__all__ = ["ConfigError", "create_app"]
