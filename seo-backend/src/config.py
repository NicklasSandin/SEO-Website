"""Configuration, read once from the environment.

Nothing in here talks to the network. `load_config` turns an environment mapping
into a plain dict that is copied into `app.config`; it fails closed (raises
`ConfigError`) for settings that would make a production deployment unsafe.
"""
from __future__ import annotations

import logging
import secrets
from typing import Mapping

log = logging.getLogger(__name__)

APP_VERSION = "0.1.0"

PLANS = {
    # Keyword limits come from the draft pricing page. There is no billing: the
    # plan only sets how many keywords one project may track.
    "starter": 10,
    "professional": 25,
    "enterprise": 50,
}

_PLACEHOLDER_SECRETS = {
    "",
    "change-me",
    "changeme",
    "secret",
    "dev",
    "development",
    "replace-me",
    "please-change-me",
}


class ConfigError(RuntimeError):
    """The environment is not a safe or valid configuration."""


def _bool(value: str | None, default: bool) -> bool:
    if value is None or value.strip() == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _int(env: Mapping[str, str], name: str, default: int, *, minimum: int = 0, maximum: int | None = None) -> int:
    raw = env.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be an integer") from exc
    if value < minimum or (maximum is not None and value > maximum):
        raise ConfigError(f"{name} must be between {minimum} and {maximum if maximum is not None else 'infinity'}")
    return value


def _float(env: Mapping[str, str], name: str, default: float, *, minimum: float = 0.0) -> float:
    raw = env.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = float(raw)
    except ValueError as exc:
        raise ConfigError(f"{name} must be a number") from exc
    if value < minimum:
        raise ConfigError(f"{name} must be at least {minimum}")
    return value


def _str(env: Mapping[str, str], name: str, default: str | None = None) -> str | None:
    raw = env.get(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip()


def load_config(env: Mapping[str, str]) -> dict:
    app_env = (_str(env, "APP_ENV", "development") or "development").lower()
    if app_env not in {"development", "production", "testing"}:
        raise ConfigError("APP_ENV must be development, production or testing")
    production = app_env == "production"

    secret_key = _str(env, "SECRET_KEY")
    if production:
        if secret_key is None or secret_key.lower() in _PLACEHOLDER_SECRETS or len(secret_key) < 32:
            raise ConfigError(
                "SECRET_KEY must be set to a random value of at least 32 characters when APP_ENV=production "
                '(generate one with: python -c "import secrets; print(secrets.token_hex(32))")'
            )
    elif secret_key is None:
        # Development/testing only: a per-process key. Sessions end on restart.
        secret_key = secrets.token_hex(32)
        log.warning("SECRET_KEY is not set; using a random key for this process. Sessions will not survive a restart.")

    cors_raw = _str(env, "CORS_ORIGINS", "") or ""
    cors_origins = tuple(o.strip().rstrip("/") for o in cors_raw.split(",") if o.strip())
    if "*" in cors_origins:
        raise ConfigError("CORS_ORIGINS must list explicit origins; '*' is not allowed because cookies are used")

    login = _str(env, "DATAFORSEO_LOGIN")
    password = _str(env, "DATAFORSEO_PASSWORD")
    if bool(login) != bool(password):
        raise ConfigError("Set both DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD, or neither")

    rank_provider = (_str(env, "RANK_PROVIDER", "auto") or "auto").lower()
    if rank_provider not in {"auto", "sample", "dataforseo"}:
        raise ConfigError("RANK_PROVIDER must be auto, sample or dataforseo")
    if rank_provider == "dataforseo" and not login:
        raise ConfigError("RANK_PROVIDER=dataforseo needs DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD")

    openai_key = _str(env, "OPENAI_API_KEY")
    report_generator = (_str(env, "REPORT_GENERATOR", "auto") or "auto").lower()
    if report_generator not in {"auto", "template", "openai"}:
        raise ConfigError("REPORT_GENERATOR must be auto, template or openai")
    if report_generator == "openai" and not openai_key:
        raise ConfigError("REPORT_GENERATOR=openai needs OPENAI_API_KEY")

    default_plan = (_str(env, "DEFAULT_PLAN", "starter") or "starter").lower()
    if default_plan not in PLANS:
        raise ConfigError(f"DEFAULT_PLAN must be one of: {', '.join(PLANS)}")

    return {
        "APP_ENV": app_env,
        "SECRET_KEY": secret_key,
        "DATABASE_URL": _str(env, "DATABASE_URL"),  # None -> sqlite file in the instance folder
        "CORS_ORIGINS": cors_origins,
        "STATIC_DIR": _str(env, "STATIC_DIR"),
        "ALLOW_REGISTRATION": _bool(env.get("ALLOW_REGISTRATION"), True),
        "TRUST_PROXY_HEADERS": _bool(env.get("TRUST_PROXY_HEADERS"), False),
        "DEFAULT_PLAN": default_plan,
        "MAX_PROJECTS_PER_USER": _int(env, "MAX_PROJECTS_PER_USER", 10, minimum=1),
        "MAX_ANALYSES_PER_USER_PER_DAY": _int(env, "MAX_ANALYSES_PER_USER_PER_DAY", 20, minimum=1),
        "LOGIN_MAX_FAILURES": _int(env, "LOGIN_MAX_FAILURES", 10, minimum=1),
        "LOGIN_FAILURE_WINDOW_SECONDS": _int(env, "LOGIN_FAILURE_WINDOW_SECONDS", 900, minimum=1),
        "REGISTER_MAX_PER_HOUR": _int(env, "REGISTER_MAX_PER_HOUR", 10, minimum=1),
        "SESSION_COOKIE_SECURE": _bool(env.get("SESSION_COOKIE_SECURE"), production),
        "SESSION_LIFETIME_HOURS": _int(env, "SESSION_LIFETIME_HOURS", 24 * 7, minimum=1),
        # Rank / SERP data
        "RANK_PROVIDER": rank_provider,
        "DATAFORSEO_LOGIN": login,
        "DATAFORSEO_PASSWORD": password,
        "DATAFORSEO_BASE_URL": _str(env, "DATAFORSEO_BASE_URL", "https://api.dataforseo.com") or "",
        "DATAFORSEO_TIMEOUT_SECONDS": _float(env, "DATAFORSEO_TIMEOUT_SECONDS", 60.0, minimum=1.0),
        "DATAFORSEO_MAX_RETRIES": _int(env, "DATAFORSEO_MAX_RETRIES", 3, minimum=0, maximum=10),
        "SERP_DEPTH": _int(env, "SERP_DEPTH", 20, minimum=10, maximum=100),
        "DEFAULT_LOCATION_NAME": _str(env, "DEFAULT_LOCATION_NAME", "Sweden"),
        "DEFAULT_LANGUAGE_CODE": _str(env, "DEFAULT_LANGUAGE_CODE", "sv"),
        # Report text
        "REPORT_GENERATOR": report_generator,
        "OPENAI_API_KEY": openai_key,
        "OPENAI_MODEL": _str(env, "OPENAI_MODEL", "gpt-4o-mini"),
        "OPENAI_TIMEOUT_SECONDS": _float(env, "OPENAI_TIMEOUT_SECONDS", 60.0, minimum=1.0),
    }
