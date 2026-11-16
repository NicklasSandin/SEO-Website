from flask import Flask

from . import auth, health, projects


def register_routes(app: Flask) -> None:
    for module in (health, auth, projects):
        app.register_blueprint(module.bp, url_prefix="/api")
