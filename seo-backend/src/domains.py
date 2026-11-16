"""Small helpers for turning URLs into comparable domain names."""
from __future__ import annotations

import re
from urllib.parse import urlsplit

_HOST_RE = re.compile(r"^(?=.{1,253}$)([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")


def normalize_host(host: str | None) -> str:
    host = (host or "").strip().lower().rstrip(".")
    return host[4:] if host.startswith("www.") else host


def host_from_url(url: str | None) -> str:
    try:
        return normalize_host(urlsplit((url or "").strip()).hostname)
    except ValueError:
        return ""


def is_valid_hostname(host: str) -> bool:
    return bool(_HOST_RE.match(host))


def domain_matches(candidate: str, target: str) -> bool:
    """True if `candidate` is the target domain or one of its subdomains."""
    candidate, target = normalize_host(candidate), normalize_host(target)
    return bool(candidate) and bool(target) and (candidate == target or candidate.endswith("." + target))


def safe_http_url(url: str | None) -> str:
    """Return the URL only if it is plain http(s); otherwise an empty string."""
    url = (url or "").strip()
    try:
        parts = urlsplit(url)
    except ValueError:
        return ""
    return url if parts.scheme in {"http", "https"} and parts.hostname else ""
