"""Password hashing, the login throttle, and the auth decorator."""
from __future__ import annotations

import time
from collections import defaultdict, deque
from functools import wraps
from threading import Lock

from flask import current_app, g, jsonify, session
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db
from .models import User

# Hashed on a miss so that "unknown email" and "wrong password" take about the same time.
_DUMMY_HASH = generate_password_hash("not-a-real-password")


def hash_password(password: str) -> str:
    return generate_password_hash(password)  # Werkzeug default: scrypt with a random salt


def verify_password(user: User | None, password: str) -> bool:
    if user is None:
        check_password_hash(_DUMMY_HASH, password)
        return False
    return check_password_hash(user.password_hash, password)


class LoginThrottle:
    """Counts recent failures per key. In-memory, so it is per process (run one worker; see README)."""

    def __init__(self, max_failures: int, window_seconds: int, clock=time.monotonic):
        self.max_failures = max_failures
        self.window = window_seconds
        self._clock = clock
        self._failures: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _prune(self, key: str) -> deque[float]:
        events = self._failures[key]
        cutoff = self._clock() - self.window
        while events and events[0] < cutoff:
            events.popleft()
        if not events:
            self._failures.pop(key, None)
            return deque()
        return events

    def blocked(self, key: str) -> bool:
        with self._lock:
            return len(self._prune(key)) >= self.max_failures

    def record_failure(self, key: str) -> None:
        with self._lock:
            self._prune(key)
            self._failures[key].append(self._clock())

    def reset(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)


def login_user(user: User) -> None:
    session.clear()
    session["uid"] = user.id
    session.permanent = True


def current_user() -> User | None:
    if "user" in g:
        return g.user
    uid = session.get("uid")
    g.user = db.session.get(User, uid) if isinstance(uid, int) else None
    return g.user


def login_required(view):
    @wraps(view)
    def wrapper(*args, **kwargs):
        if current_user() is None:
            return jsonify({"error": "Sign in to continue.", "code": "unauthenticated"}), 401
        return view(*args, **kwargs)

    return wrapper


def plan_keyword_limit(user: User) -> int:
    from .config import PLANS

    return PLANS.get(user.plan, PLANS[current_app.config["DEFAULT_PLAN"]])
