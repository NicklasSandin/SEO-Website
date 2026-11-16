"""DataForSEO client against a fake HTTP adapter. Response bodies follow the shapes in the
official documentation; they are hand-written, not recorded from the live API."""
import base64
import json
import logging

import pytest
import requests

from src.providers import (
    DataForSEOClient,
    ProviderAuthError,
    ProviderError,
    ProviderPaymentError,
    ProviderRateLimitError,
)
from src.providers.dataforseo import parse_instant_page

from .conftest import api_ok, make_response, session_with

LOGIN = "api-login@example.com"
PASSWORD = "very-secret-api-password"
KW = dict(location_name="Sweden", language_code="sv")


def client(*queue, **kwargs):
    session, adapter = session_with(*queue)
    sleeps: list[float] = []
    kwargs.setdefault("sleep", sleeps.append)
    c = DataForSEOClient(LOGIN, PASSWORD, session=session, **kwargs)
    return c, adapter, sleeps


SERP_BODY = api_ok(
    [
        {
            "keyword": "boiler repair",
            "type": "organic",
            "items_count": 5,
            "items": [
                {"type": "paid", "rank_group": 1, "rank_absolute": 1, "domain": "ads.example.com", "url": "https://ads.example.com/", "title": "Ad"},
                {"type": "organic", "rank_group": 1, "rank_absolute": 2, "domain": "www.Rival.se", "url": "https://www.rival.se/a", "title": "Rival"},
                {"type": "people_also_ask", "rank_group": 1, "rank_absolute": 3},
                {"type": "organic", "rank_group": 2, "rank_absolute": 5, "domain": "example.org", "url": "https://example.org/boilers", "title": "Mine"},
                {"type": "organic", "rank_group": 3, "rank_absolute": 6, "domain": "bad.example", "url": "javascript:alert(1)", "title": "Bad link"},
            ],
        }
    ]
)


def test_serp_request_shape_and_basic_auth():
    c, adapter, _ = client(make_response(body=SERP_BODY))
    c.get_serp("boiler repair", depth=20, **KW)
    (request,) = adapter.requests
    assert request.method == "POST"
    assert request.url == "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"
    assert json.loads(request.body) == [
        {
            "keyword": "boiler repair",
            "location_name": "Sweden",
            "language_code": "sv",
            "depth": 20,
            "device": "desktop",
            "os": "windows",
        }
    ]
    expected = "Basic " + base64.b64encode(f"{LOGIN}:{PASSWORD}".encode()).decode()
    assert request.headers["Authorization"] == expected


def test_serp_keeps_only_organic_items_and_uses_rank_group():
    c, _, _ = client(make_response(body=SERP_BODY))
    serp = c.get_serp("boiler repair", depth=20, **KW)
    assert [(i.rank, i.rank_absolute, i.domain) for i in serp.items] == [
        (1, 2, "rival.se"),
        (2, 5, "example.org"),
        (3, 6, "bad.example"),
    ]
    assert serp.items[2].url == ""  # non-http(s) URLs are dropped, never passed on to the UI


def test_serp_no_results_status_is_an_empty_result_not_an_error():
    body = api_ok(None, status_code=40102)
    body["tasks"][0]["status_message"] = "No Search Results."
    c, _, _ = client(make_response(body=body))
    assert c.get_serp("zzzz", depth=10, **KW).items == []


def test_keyword_metrics_combines_volume_and_difficulty():
    volume = api_ok(
        [{"keyword": "boiler repair", "search_volume": 880, "competition": "LOW"}, {"keyword": "plumber", "search_volume": None}],
        path="keywords_data/google_ads/search_volume/live",
    )
    difficulty = api_ok(
        [{"se_type": "google", "items_count": 2, "items": [{"keyword": "boiler repair", "keyword_difficulty": 37}, {"keyword": "plumber", "keyword_difficulty": 52}]}],
        path="dataforseo_labs/google/bulk_keyword_difficulty/live",
    )
    c, adapter, _ = client(make_response(body=volume), make_response(body=difficulty))
    result = c.get_keyword_metrics(["Boiler Repair", "plumber"], **KW)
    assert result.metrics["boiler repair"].search_volume == 880
    assert result.metrics["boiler repair"].difficulty == 37
    assert result.metrics["plumber"].search_volume is None
    assert result.metrics["plumber"].difficulty == 52
    assert result.warnings == []
    assert adapter.requests[0].url.endswith("/v3/keywords_data/google_ads/search_volume/live")
    assert adapter.requests[1].url.endswith("/v3/dataforseo_labs/google/bulk_keyword_difficulty/live")
    sent = json.loads(adapter.requests[0].body)[0]
    assert sent == {"keywords": ["Boiler Repair", "plumber"], "location_name": "Sweden", "language_code": "sv"}


def test_one_failed_metrics_call_becomes_a_warning_and_keeps_the_other():
    volume = api_ok([{"keyword": "plumber", "search_volume": 100}], path="keywords_data/google_ads/search_volume/live")
    bad = api_ok(None, status_code=40501)
    bad["tasks"][0]["status_message"] = "Invalid Field: 'x'."
    c, _, _ = client(make_response(body=volume), make_response(body=bad))
    result = c.get_keyword_metrics(["plumber"], **KW)
    assert result.metrics["plumber"].search_volume == 100
    assert result.metrics["plumber"].difficulty is None
    assert len(result.warnings) == 1 and "difficulty" in result.warnings[0].lower()


def test_http_401_is_an_auth_error_and_is_not_retried():
    c, adapter, sleeps = client(make_response(status=401, body={"status_code": 40100, "status_message": "You are not authorized"}))
    with pytest.raises(ProviderAuthError):
        c.get_serp("x", depth=10, **KW)
    assert len(adapter.requests) == 1 and sleeps == []


def test_status_40100_in_a_200_response_is_an_auth_error():
    body = {"status_code": 40100, "status_message": "You are not authorized to access this resource.", "tasks": []}
    c, adapter, _ = client(make_response(body=body))
    with pytest.raises(ProviderAuthError):
        c.get_serp("x", depth=10, **KW)
    assert len(adapter.requests) == 1


@pytest.mark.parametrize("code", [40200, 40210, 40203])
def test_payment_problems_are_not_retried(code):
    body = api_ok(None, status_code=code)
    c, adapter, _ = client(make_response(body=body))
    with pytest.raises(ProviderPaymentError):
        c.get_serp("x", depth=10, **KW)
    assert len(adapter.requests) == 1


def test_http_402_is_a_payment_error():
    c, _, _ = client(make_response(status=402, body={}))
    with pytest.raises(ProviderPaymentError):
        c.get_serp("x", depth=10, **KW)


def test_429_is_retried_honouring_retry_after_then_succeeds():
    c, adapter, sleeps = client(
        make_response(status=429, body={}, headers={"Retry-After": "7"}),
        make_response(body=SERP_BODY),
    )
    serp = c.get_serp("boiler repair", depth=20, **KW)
    assert len(serp.items) == 3
    assert len(adapter.requests) == 2
    assert sleeps == [7.0]


def test_rate_limit_status_is_retried_with_exponential_backoff_then_raises():
    limited = api_ok(None, status_code=40202)
    c, adapter, sleeps = client(make_response(body=limited), max_retries=3, backoff_base=1.0)
    with pytest.raises(ProviderRateLimitError):
        c.get_serp("x", depth=10, **KW)
    assert len(adapter.requests) == 4  # first try + 3 retries
    assert sleeps == [1.0, 2.0, 4.0]


def test_retry_after_is_capped():
    c, _, sleeps = client(
        make_response(status=429, body={}, headers={"Retry-After": "100000"}),
        make_response(body=SERP_BODY),
    )
    c.get_serp("boiler repair", depth=20, **KW)
    assert sleeps == [60.0]


def test_server_errors_are_retried():
    c, adapter, sleeps = client(make_response(status=503, body={}), make_response(body=SERP_BODY))
    c.get_serp("boiler repair", depth=20, **KW)
    assert len(adapter.requests) == 2 and len(sleeps) == 1


def test_transient_status_in_body_is_retried():
    timeout = api_ok(None, status_code=50401)
    c, adapter, _ = client(make_response(body=timeout), make_response(body=SERP_BODY))
    c.get_serp("boiler repair", depth=20, **KW)
    assert len(adapter.requests) == 2


def test_network_errors_are_retried_then_reported_without_details():
    c, adapter, sleeps = client(requests.exceptions.ConnectionError("dns failure for api.dataforseo.com"), max_retries=2)
    with pytest.raises(ProviderError) as info:
        c.get_serp("x", depth=10, **KW)
    assert len(adapter.requests) == 3 and len(sleeps) == 2
    assert "dns failure" not in str(info.value)


def test_request_errors_are_not_retried():
    body = api_ok(None, status_code=40501)
    body["tasks"][0]["status_message"] = "Invalid Field: 'depth'."
    c, adapter, _ = client(make_response(body=body))
    with pytest.raises(ProviderError) as info:
        c.get_serp("x", depth=10, **KW)
    assert not info.value.retryable and info.value.code == 40501 and "Invalid Field" in str(info.value)
    assert len(adapter.requests) == 1


def test_invalid_json_and_empty_tasks_are_provider_errors():
    c, _, _ = client(make_response(text="<html>gateway</html>"))
    with pytest.raises(ProviderError):
        c.get_serp("x", depth=10, **KW)
    c, _, _ = client(make_response(body={"status_code": 20000, "tasks": []}))
    with pytest.raises(ProviderError):
        c.get_serp("x", depth=10, **KW)


def test_credentials_never_appear_in_repr_errors_or_logs(caplog):
    caplog.set_level(logging.DEBUG)
    c, _, _ = client(make_response(status=401, body={}))
    assert PASSWORD not in repr(c) and LOGIN not in repr(c)
    with pytest.raises(ProviderAuthError) as info:
        c.get_serp("x", depth=10, **KW)
    assert PASSWORD not in str(info.value) and LOGIN not in str(info.value)
    assert PASSWORD not in caplog.text and LOGIN not in caplog.text


def test_missing_credentials_are_rejected_up_front():
    with pytest.raises(ValueError):
        DataForSEOClient("", "")


# ---------------------------------------------------------------- on_page / instant_pages

HTML_ITEM = {
    "resource_type": "html",
    "status_code": 200,
    "onpage_score": 81.4,
    "meta": {"title": "Home"},
    "checks": {
        "no_description": True,
        "no_h1_tag": False,
        "is_http": True,
        "no_favicon": True,
        "is_4xx_code": False,
        "canonical": True,
        "high_loading_time": None,
        "unknown_future_check": True,
    },
}


def test_audit_maps_flagged_checks_to_sorted_issues():
    body = api_ok([{"crawl_progress": "finished", "items_count": 1, "items": [HTML_ITEM]}], path="on_page/instant_pages")
    c, adapter, _ = client(make_response(body=body))
    audit = c.audit_page("https://example.org")
    assert adapter.requests[0].url == "https://api.dataforseo.com/v3/on_page/instant_pages"
    assert json.loads(adapter.requests[0].body) == [{"url": "https://example.org"}]
    assert audit.onpage_score == 81.4
    assert [(i.id, i.severity) for i in audit.issues] == [("is_http", "warning"), ("no_description", "warning"), ("no_favicon", "info")]


def test_audit_reports_broken_and_redirecting_pages():
    broken = parse_instant_page("https://x.example", {"result": [{"items": [{"resource_type": "broken", "status_code": 404}]}]})
    assert broken.issues[0].severity == "critical" and "404" in broken.issues[0].detail
    redirect = parse_instant_page("https://x.example", {"result": [{"items": [{"resource_type": "redirect", "location": "https://y.example/"}]}]})
    assert redirect.issues[0].id == "is_redirect" and "https://y.example/" in redirect.issues[0].detail


def test_audit_without_items_is_an_error():
    with pytest.raises(ProviderError):
        parse_instant_page("https://x.example", {"result": [{"items": []}]})
