from __future__ import annotations

from typing import Any

from flask import jsonify, request

from ..extensions import db
from ..models import Project
from ..security import current_user
from ..validation import ValidationError, require_object


def error(message: str, code: str, status: int, **extra: Any):
    body = {"error": message, "code": code}
    body.update(extra)
    return jsonify(body), status


def json_body(*, required: bool = True) -> dict:
    """The parsed JSON object body. Raises ValidationError if it is missing or not an object."""
    if not request.get_data(cache=True):
        if required:
            raise ValidationError("Send a JSON body.")
        return {}
    if request.mimetype != "application/json":
        raise ValidationError("Send the body as JSON with Content-Type: application/json.")
    data = request.get_json(silent=True)
    if data is None:
        raise ValidationError("The request body is not valid JSON.")
    return require_object(data)


def owned_project(project_id: int) -> Project | None:
    """The project if it belongs to the signed-in user, else None (callers answer 404 either way)."""
    user = current_user()
    return Project.query.filter_by(id=project_id, user_id=user.id).first() if user else None


def not_found(what: str = "Not found"):
    return error(what, "not_found", 404)


__all__ = ["db", "error", "json_body", "not_found", "owned_project"]
