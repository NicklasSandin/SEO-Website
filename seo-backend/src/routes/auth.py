from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request, session
from sqlalchemy.exc import IntegrityError

from ..extensions import db
from ..models import User
from ..security import current_user, hash_password, login_required, login_user, verify_password
from ..validation import validate_email, validate_password, validate_plan
from .common import error, json_body

bp = Blueprint("auth", __name__)


def _throttle_keys(email: str) -> list[str]:
    ip = request.remote_addr or "unknown"
    return [f"ip:{ip}", f"acct:{email}:{ip}"]


@bp.post("/auth/register")
def register():
    if not current_app.config["ALLOW_REGISTRATION"]:
        return error("Registration is closed.", "registration_closed", 403)
    reg_throttle = current_app.extensions["siktio_register_throttle"]
    reg_key = f"reg:{request.remote_addr or 'unknown'}"
    if reg_throttle.blocked(reg_key):
        return error("Too many sign-ups from this address. Try again later.", "too_many_attempts", 429)
    reg_throttle.record_failure(reg_key)  # counts every attempt, not only failures
    data = json_body()
    email = validate_email(data.get("email"))
    password = validate_password(data.get("password"))
    plan = validate_plan(data.get("plan"), current_app.config["DEFAULT_PLAN"])
    if User.query.filter_by(email=email).first():
        # A registration form can reveal that an address is taken; that is accepted for this prototype.
        return error("An account with this email already exists.", "email_taken", 409, field="email")
    user = User(email=email, password_hash=hash_password(password), plan=plan)
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return error("An account with this email already exists.", "email_taken", 409, field="email")
    login_user(user)
    return jsonify({"user": user.to_dict()}), 201


@bp.post("/auth/login")
def login():
    throttle = current_app.extensions["siktio_login_throttle"]
    data = json_body()
    email_raw = data.get("email")
    password = data.get("password")
    email = email_raw.strip().lower() if isinstance(email_raw, str) else ""
    keys = _throttle_keys(email)
    if any(throttle.blocked(k) for k in keys):
        return error("Too many failed sign-in attempts. Try again later.", "too_many_attempts", 429)
    user = User.query.filter_by(email=email).first() if email else None
    if not isinstance(password, str) or not verify_password(user, password[:128]):
        for k in keys:
            throttle.record_failure(k)
        return error("Invalid email or password.", "invalid_credentials", 401)
    for k in keys:
        throttle.reset(k)
    login_user(user)
    return jsonify({"user": user.to_dict()})


@bp.post("/auth/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})


@bp.get("/auth/me")
@login_required
def me():
    return jsonify({"user": current_user().to_dict()})

