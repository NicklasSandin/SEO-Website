"""Input validation. Every function raises ValidationError with a message safe to show to the user."""
from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlsplit

from .config import PLANS
from .domains import is_valid_hostname, normalize_host

EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,255}\.[^@\s.]{2,63}$")
LOCATION_RE = re.compile(r"^[A-Za-z][A-Za-z ,.'()-]{1,98}$")
LANGUAGE_RE = re.compile(r"^[a-z]{2,3}(-[A-Za-z]{2,4})?$")
KEYWORD_RE = re.compile(r"^[^\x00-\x1f\x7f<>{}\[\]\\|]+$")

PASSWORD_MIN = 10
PASSWORD_MAX = 128  # also bounds the work the password hash has to do
KEYWORD_MAX_CHARS = 80  # DataForSEO's search volume endpoint limit
KEYWORD_MAX_WORDS = 10


class ValidationError(ValueError):
    def __init__(self, message: str, field: str | None = None):
        super().__init__(message)
        self.field = field


def require_object(data: Any) -> dict:
    if not isinstance(data, dict):
        raise ValidationError("Request body must be a JSON object.")
    return data


def validate_email(value: Any) -> str:
    if not isinstance(value, str):
        raise ValidationError("Email is required.", "email")
    email = value.strip().lower()
    if len(email) > 254 or not EMAIL_RE.match(email):
        raise ValidationError("Enter a valid email address.", "email")
    return email


def validate_password(value: Any) -> str:
    if not isinstance(value, str) or not (PASSWORD_MIN <= len(value) <= PASSWORD_MAX):
        raise ValidationError(f"Password must be between {PASSWORD_MIN} and {PASSWORD_MAX} characters.", "password")
    if value.strip() == "":
        raise ValidationError("Password cannot be only spaces.", "password")
    return value


def validate_plan(value: Any, default: str) -> str:
    if value is None:
        return default
    if not isinstance(value, str) or value.lower() not in PLANS:
        raise ValidationError(f"Plan must be one of: {', '.join(PLANS)}.", "plan")
    return value.lower()


def validate_name(value: Any) -> str:
    if not isinstance(value, str) or not (1 <= len(value.strip()) <= 100):
        raise ValidationError("Name must be 1 to 100 characters.", "name")
    name = value.strip()
    if re.search(r"[\x00-\x1f\x7f<>]", name):
        raise ValidationError("Name contains characters that are not allowed.", "name")
    return name


def validate_website_url(value: Any) -> tuple[str, str]:
    """Returns (normalised url, domain). Only plain http(s) URLs for a real hostname are accepted."""
    if not isinstance(value, str) or not value.strip():
        raise ValidationError("Website URL is required.", "website_url")
    raw = value.strip()
    if len(raw) > 255:
        raise ValidationError("Website URL is too long.", "website_url")
    if "://" not in raw:
        raw = "https://" + raw
    try:
        parts = urlsplit(raw)
        host = normalize_host(parts.hostname)
        port = parts.port
    except ValueError:
        raise ValidationError("Enter a valid website URL.", "website_url") from None
    if parts.scheme not in {"http", "https"} or parts.username or parts.password or port is not None:
        raise ValidationError("Use a plain http:// or https:// address without credentials or a port.", "website_url")
    if not is_valid_hostname(host):
        raise ValidationError("Enter a valid domain name, for example https://example.com.", "website_url")
    path = parts.path.rstrip("/") if parts.path != "/" else ""
    url = f"{parts.scheme}://{parts.hostname}{path}"
    return url, host


def validate_keywords(value: Any, limit: int) -> list[str]:
    if isinstance(value, str):
        value = value.split(",")
    if not isinstance(value, list) or not value:
        raise ValidationError("Enter at least one keyword.", "keywords")
    seen: dict[str, None] = {}
    for item in value:
        if not isinstance(item, str):
            raise ValidationError("Keywords must be text.", "keywords")
        keyword = re.sub(r"\s+", " ", item).strip().lower()
        if not keyword:
            continue
        if len(keyword) > KEYWORD_MAX_CHARS or len(keyword.split(" ")) > KEYWORD_MAX_WORDS or not KEYWORD_RE.match(keyword):
            raise ValidationError(
                f"Each keyword can be at most {KEYWORD_MAX_CHARS} characters and {KEYWORD_MAX_WORDS} words, without special symbols.",
                "keywords",
            )
        seen.setdefault(keyword, None)
    keywords = list(seen)
    if not keywords:
        raise ValidationError("Enter at least one keyword.", "keywords")
    if len(keywords) > limit:
        raise ValidationError(f"Your plan allows up to {limit} keywords per project.", "keywords")
    return keywords


def validate_location(value: Any, default: str) -> str:
    if value is None or value == "":
        return default
    if not isinstance(value, str) or not LOCATION_RE.match(value.strip()):
        raise ValidationError("Location must be a place name such as Sweden.", "location_name")
    return value.strip()


def validate_language(value: Any, default: str) -> str:
    if value is None or value == "":
        return default
    if not isinstance(value, str) or not LANGUAGE_RE.match(value.strip()):
        raise ValidationError("Language must be a code such as sv or en.", "language_code")
    return value.strip()
