"""DataForSEO client (https://docs.dataforseo.com/v3/).

Endpoints used, all "Live" (synchronous) endpoints called with HTTP Basic auth:

* ``POST /v3/serp/google/organic/live/advanced``              Google organic results per keyword
* ``POST /v3/keywords_data/google_ads/search_volume/live``    monthly search volume
* ``POST /v3/dataforseo_labs/google/bulk_keyword_difficulty/live``  keyword difficulty (0-100)
* ``POST /v3/on_page/instant_pages``                          on-page technical checks for one URL

Request and response shapes, error codes and limits were taken from the official documentation
pages for those endpoints and from the "Errors" appendix. They have NOT been exercised against the
real API (no credentials were available when this was written); the unit tests run against
recorded-by-hand fixtures through a fake HTTP adapter.

Behaviour worth knowing:

* Live endpoints accept one task per POST, so each call here sends a one-element array.
* The API answers HTTP 200 for most errors; the real result is the ``status_code`` in the JSON
  body (20000 = ok) and again inside ``tasks[0]``.
* Rate limits (HTTP 429, status 40202) and concurrency limits (40209) and transient server
  errors are retried with exponential backoff, honouring ``Retry-After``. Auth (40100/401),
  payment (40200/40210/402) and request errors are not retried.
* Credentials are only ever passed to ``requests`` as ``auth=(login, password)``; they are not
  logged and not included in exception messages.
"""
from __future__ import annotations

import logging
import re
import time
from typing import Any, Callable

import requests

from ..domains import host_from_url, normalize_host, safe_http_url
from .base import (
    AuditIssue,
    KeywordMetrics,
    MetricsResult,
    OrganicResult,
    PageAudit,
    ProviderAuthError,
    ProviderError,
    ProviderPaymentError,
    ProviderRateLimitError,
    RankProvider,
    SerpResult,
)

log = logging.getLogger(__name__)

DEFAULT_BASE_URL = "https://api.dataforseo.com"

SERP_PATH = "serp/google/organic/live/advanced"
SEARCH_VOLUME_PATH = "keywords_data/google_ads/search_volume/live"
KEYWORD_DIFFICULTY_PATH = "dataforseo_labs/google/bulk_keyword_difficulty/live"
ON_PAGE_PATH = "on_page/instant_pages"

STATUS_OK = 20000
STATUS_NO_RESULTS = 40102

AUTH_CODES = {40100, 40104, 40201, 40207}
PAYMENT_CODES = {40200, 40203, 40210}
RATE_LIMIT_CODES = {40202, 40209}
# 40101 search engine error, 40103 resubmit, 50000 internal, 50301 third-party source down,
# 50303 update in progress, 50401 live task timed out, 50402 target page slow.
RETRYABLE_CODES = {40101, 40103, 50000, 50301, 50303, 50401, 50402}

MAX_BACKOFF_SECONDS = 60.0

# on_page `checks` flags that indicate a problem when true: (severity, title, detail).
CHECK_RULES: dict[str, tuple[str, str, str]] = {
    "is_broken": ("critical", "Page is broken", "The page could not be loaded correctly."),
    "is_4xx_code": ("critical", "Page returns a 4xx error", "The page answers with a client error status code."),
    "is_5xx_code": ("critical", "Page returns a 5xx error", "The page answers with a server error status code."),
    "no_title": ("critical", "Missing title tag", "The page has no <title>, which search results use as the headline."),
    "is_http": ("warning", "Served over HTTP", "The page is not served over HTTPS."),
    "no_description": ("warning", "Missing meta description", "The page has no meta description."),
    "title_too_long": ("warning", "Title is too long", "The title is long enough to be cut off in search results."),
    "title_too_short": ("warning", "Title is too short", "The title is very short and may not describe the page."),
    "no_h1_tag": ("warning", "No H1 heading", "The page has no top-level heading."),
    "duplicate_title_tag": ("warning", "Duplicate title tag", "The page has more than one title tag."),
    "duplicate_meta_tags": ("warning", "Duplicate meta tags", "The page repeats meta tags."),
    "https_to_http_links": ("warning", "HTTPS page links to HTTP", "An HTTPS page links to or loads HTTP resources."),
    "high_loading_time": ("warning", "Slow loading time", "The page takes long to load."),
    "high_waiting_time": ("warning", "Slow server response", "The server takes long to start responding."),
    "low_content_rate": ("warning", "Low share of text content", "Little of the page's HTML is readable text."),
    "low_character_count": ("warning", "Very little text", "The page has very few characters of text."),
    "no_image_alt": ("warning", "Images without alt text", "Some images have no alt attribute."),
    "large_page_size": ("warning", "Large page size", "The page is large to download."),
    "size_greater_than_3mb": ("warning", "Page over 3 MB", "The page is larger than 3 MB."),
    "has_render_blocking_resources": ("warning", "Render-blocking resources", "Scripts or styles delay first paint."),
    "is_redirect": ("warning", "Page redirects", "The URL redirects somewhere else."),
    "has_meta_refresh_redirect": ("warning", "Meta refresh redirect", "The page redirects with a meta refresh tag."),
    "no_doctype": ("warning", "No doctype", "The page has no HTML doctype declaration."),
    "irrelevant_title": ("warning", "Title may not match content", "The title seems unrelated to the page content."),
    "irrelevant_description": ("warning", "Description may not match content", "The meta description seems unrelated to the content."),
    "no_content_encoding": ("info", "No compression", "The response is not compressed (no content-encoding)."),
    "no_favicon": ("info", "No favicon", "The page has no favicon."),
    "no_image_title": ("info", "Images without title attribute", "Some images have no title attribute."),
    "deprecated_html_tags": ("info", "Deprecated HTML tags", "The page uses deprecated HTML tags."),
    "low_readability_rate": ("info", "Low readability", "The text scores low on readability."),
    "flash": ("warning", "Uses Flash", "The page embeds Flash content."),
    "frame": ("info", "Uses frames", "The page uses frames."),
    "lorem_ipsum": ("warning", "Placeholder text", "The page contains lorem ipsum placeholder text."),
}

_SEVERITY_ORDER = {"critical": 0, "warning": 1, "info": 2}


def _clean_message(value: Any) -> str:
    text = re.sub(r"[\x00-\x1f\x7f]", " ", str(value or "")).strip()
    return text[:200]


class DataForSEOClient(RankProvider):
    name = "dataforseo"
    is_sample = False

    def __init__(
        self,
        login: str,
        password: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        session: requests.Session | None = None,
        timeout: float = 60.0,
        max_retries: int = 3,
        backoff_base: float = 1.0,
        sleep: Callable[[float], None] = time.sleep,
    ):
        if not login or not password:
            raise ValueError("DataForSEO login and password are required")
        self._auth = (login, password)
        self.base_url = base_url.rstrip("/")
        self.session = session or requests.Session()
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff_base = backoff_base
        self._sleep = sleep

    def __repr__(self) -> str:  # never show credentials
        return f"<DataForSEOClient base_url={self.base_url!r}>"

    # ------------------------------------------------------------------ HTTP layer

    def _post(self, path: str, task: dict, *, tolerate_codes: frozenset[int] = frozenset()) -> dict:
        """POST one task and return the ``tasks[0]`` object. Retries transient failures."""
        url = f"{self.base_url}/v3/{path}"
        attempt = 0
        while True:
            try:
                response = self.session.post(url, json=[task], auth=self._auth, timeout=self.timeout)
                return self._interpret(response, path, tolerate_codes)
            except requests.exceptions.RequestException as exc:
                # Log only the exception class: the message can contain the URL.
                log.warning("DataForSEO %s: network error (%s)", path, type(exc).__name__)
                error: ProviderError = ProviderError(
                    "Could not reach DataForSEO (network error or timeout).", retryable=True
                )
            except ProviderError as exc:
                error = exc
            if not error.retryable or attempt >= self.max_retries:
                raise error
            delay = self._delay(attempt, error)
            log.info("DataForSEO %s: retrying in %.1fs (attempt %d)", path, delay, attempt + 1)
            self._sleep(delay)
            attempt += 1

    def _delay(self, attempt: int, error: ProviderError) -> float:
        retry_after = getattr(error, "retry_after", None)
        if retry_after is not None:
            return min(MAX_BACKOFF_SECONDS, max(0.0, retry_after))
        return min(MAX_BACKOFF_SECONDS, self.backoff_base * (2**attempt))

    def _interpret(self, response: requests.Response, path: str, tolerate_codes: frozenset[int]) -> dict:
        status = response.status_code
        if status in (401, 403):
            raise ProviderAuthError("DataForSEO rejected the configured credentials.", code=status)
        if status == 402:
            raise ProviderPaymentError("DataForSEO reports a payment problem (check the account balance).", code=status)
        if status == 429:
            retry_after: float | None = None
            try:
                retry_after = float(response.headers.get("Retry-After", ""))
            except (TypeError, ValueError):
                pass
            raise ProviderRateLimitError("DataForSEO rate limit exceeded.", code=status, retry_after=retry_after)
        if status >= 500:
            raise ProviderError(f"DataForSEO server error (HTTP {status}).", code=status, retryable=True)
        if status != 200:
            raise ProviderError(f"Unexpected DataForSEO response (HTTP {status}).", code=status)

        try:
            body = response.json()
        except ValueError:
            raise ProviderError("DataForSEO returned a response that is not valid JSON.") from None
        if not isinstance(body, dict):
            raise ProviderError("DataForSEO returned an unexpected response shape.")

        top_code = body.get("status_code")
        if top_code != STATUS_OK and top_code not in tolerate_codes:
            self._raise_for_code(top_code, body.get("status_message"), path)

        tasks = body.get("tasks")
        if not isinstance(tasks, list) or not tasks or not isinstance(tasks[0], dict):
            raise ProviderError("DataForSEO returned no task in the response.")
        task = tasks[0]
        task_code = task.get("status_code")
        if task_code != STATUS_OK and task_code not in tolerate_codes:
            self._raise_for_code(task_code, task.get("status_message"), path)
        return task

    @staticmethod
    def _raise_for_code(code: Any, message: Any, path: str) -> None:
        text = f"DataForSEO error {code}: {_clean_message(message)}"
        log.warning("DataForSEO %s failed with status_code=%s", path, code)
        if code in AUTH_CODES:
            raise ProviderAuthError(text, code=code)
        if code in PAYMENT_CODES:
            raise ProviderPaymentError(text, code=code)
        if code in RATE_LIMIT_CODES:
            raise ProviderRateLimitError(text, code=code)
        raise ProviderError(text, code=code if isinstance(code, int) else None, retryable=code in RETRYABLE_CODES)

    # ------------------------------------------------------------------ SERP

    def get_serp(
        self,
        keyword: str,
        *,
        location_name: str,
        language_code: str,
        depth: int,
        target_domain: str | None = None,
    ) -> SerpResult:
        task = {
            "keyword": keyword,
            "location_name": location_name,
            "language_code": language_code,
            "depth": depth,
            "device": "desktop",
            "os": "windows",
        }
        response = self._post(SERP_PATH, task, tolerate_codes=frozenset({STATUS_NO_RESULTS}))
        return parse_serp(keyword, response)

    # ------------------------------------------------------------------ keyword metrics

    def get_keyword_metrics(
        self, keywords: list[str], *, location_name: str, language_code: str
    ) -> MetricsResult:
        base = {"keywords": keywords, "location_name": location_name, "language_code": language_code}
        volumes: dict[str, int | None] = {}
        difficulties: dict[str, int | None] = {}
        warnings: list[str] = []

        # Auth, payment and rate-limit errors are not "partial": they propagate to the caller.
        try:
            volumes = parse_search_volume(self._post(SEARCH_VOLUME_PATH, dict(base)))
        except (ProviderAuthError, ProviderPaymentError, ProviderRateLimitError):
            raise
        except ProviderError as exc:
            warnings.append(f"Search volume is unavailable: {exc}")
        try:
            difficulties = parse_keyword_difficulty(self._post(KEYWORD_DIFFICULTY_PATH, dict(base)))
        except (ProviderAuthError, ProviderPaymentError, ProviderRateLimitError):
            raise
        except ProviderError as exc:
            warnings.append(f"Keyword difficulty is unavailable: {exc}")

        metrics = {
            kw.lower(): KeywordMetrics(search_volume=volumes.get(kw.lower()), difficulty=difficulties.get(kw.lower()))
            for kw in keywords
        }
        return MetricsResult(metrics=metrics, warnings=warnings)

    # ------------------------------------------------------------------ on-page audit

    def audit_page(self, url: str) -> PageAudit:
        return parse_instant_page(url, self._post(ON_PAGE_PATH, {"url": url}))


# ---------------------------------------------------------------------- response mapping (pure)


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    return None


def parse_serp(keyword: str, task: dict) -> SerpResult:
    results = task.get("result") or []
    raw_items = results[0].get("items") if results and isinstance(results[0], dict) else None
    items: list[OrganicResult] = []
    for raw in raw_items or []:
        if not isinstance(raw, dict) or raw.get("type") != "organic":
            continue
        rank = _as_int(raw.get("rank_group"))
        url = safe_http_url(raw.get("url"))
        domain = normalize_host(raw.get("domain")) or host_from_url(url)
        if rank is None or not domain:
            continue
        items.append(
            OrganicResult(
                rank=rank,
                rank_absolute=_as_int(raw.get("rank_absolute")),
                domain=domain,
                url=url,
                title=str(raw.get("title") or "")[:300],
            )
        )
    items.sort(key=lambda item: item.rank)
    return SerpResult(keyword=keyword, items=items)


def parse_search_volume(task: dict) -> dict[str, int | None]:
    out: dict[str, int | None] = {}
    for raw in task.get("result") or []:
        if isinstance(raw, dict) and isinstance(raw.get("keyword"), str):
            out[raw["keyword"].lower()] = _as_int(raw.get("search_volume"))
    return out


def parse_keyword_difficulty(task: dict) -> dict[str, int | None]:
    out: dict[str, int | None] = {}
    for result in task.get("result") or []:
        for raw in (result or {}).get("items") or []:
            if isinstance(raw, dict) and isinstance(raw.get("keyword"), str):
                out[raw["keyword"].lower()] = _as_int(raw.get("keyword_difficulty"))
    return out


def parse_instant_page(url: str, task: dict) -> PageAudit:
    results = task.get("result") or []
    raw_items = results[0].get("items") if results and isinstance(results[0], dict) else None
    if not raw_items or not isinstance(raw_items[0], dict):
        raise ProviderError("DataForSEO returned no page data for the audit.")
    item = raw_items[0]
    resource_type = item.get("resource_type")

    if resource_type == "redirect":
        target = safe_http_url(item.get("location"))
        detail = f"The URL redirects to {target}." if target else "The URL redirects elsewhere."
        return PageAudit(url=url, onpage_score=None, issues=[AuditIssue("is_redirect", "warning", "Page redirects", detail)])
    if resource_type == "broken":
        status = _as_int(item.get("status_code"))
        detail = f"The page could not be loaded (HTTP status {status})." if status else "The page could not be loaded."
        return PageAudit(url=url, onpage_score=None, issues=[AuditIssue("is_broken", "critical", "Page is broken", detail)])

    checks = item.get("checks") if isinstance(item.get("checks"), dict) else {}
    issues = [
        AuditIssue(name, severity, title, detail)
        for name, (severity, title, detail) in CHECK_RULES.items()
        if checks.get(name) is True
    ]
    issues.sort(key=lambda issue: (_SEVERITY_ORDER[issue.severity], issue.id))
    score = item.get("onpage_score")
    return PageAudit(
        url=url,
        onpage_score=float(score) if isinstance(score, (int, float)) and not isinstance(score, bool) else None,
        issues=issues,
    )
