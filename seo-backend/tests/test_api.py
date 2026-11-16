import json

import pytest

from src.config import PLANS
from src.providers import (
    ProviderAuthError,
    ProviderError,
    ProviderPaymentError,
    ProviderRateLimitError,
    SampleProvider,
)

from .conftest import create_project, make_env, new_client, register
from src.app import create_app

LLM_REPLY = {
    "executive_summary": "Summary.",
    "ranking_analysis": "Ranking.",
    "competitor_analysis": "Competitors.",
    "content_suggestions": [{"title": "T", "keyword": "k", "type": "Article", "description": "D"}],
    "technical_recommendations": ["Do a thing."],
    "action_plan": [{"task": "Task", "priority": "Low", "rationale": "Why."}],
}


# ---------------------------------------------------------------- health & basics


def test_health_reports_modes_without_secrets(client, app):
    body = client.get("/api/health").get_json()
    assert body["status"] == "ok" and body["database"] == "ok"
    assert body["rank_provider"] == "sample" and body["rank_data_is_sample"] is True
    assert body["report_generator"] == "template"
    assert app.config["SECRET_KEY"] not in json.dumps(body)


def test_health_reflects_configured_services_without_leaking_keys():
    app = create_app(
        make_env(DATAFORSEO_LOGIN="login-xyz", DATAFORSEO_PASSWORD="pass-xyz", OPENAI_API_KEY="sk-abc-xyz"),
        llm=lambda *a, **k: "{}",
    )
    text = new_client(app).get("/api/health").get_data(as_text=True)
    body = json.loads(text)
    assert body["rank_provider"] == "dataforseo" and body["rank_data_is_sample"] is False
    assert body["report_generator"] == "openai"
    assert "xyz" not in text and "sk-abc" not in text


def test_unknown_api_paths_and_methods_return_json(client):
    r = client.get("/api/nope")
    assert r.status_code == 404 and r.get_json()["code"] == "not_found"
    r = client.delete("/api/health")
    assert r.status_code == 405 and r.is_json


def test_security_headers(client):
    r = client.get("/api/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["Cache-Control"] == "no-store"
    page = client.get("/")
    assert "frame-ancestors 'none'" in page.headers["Content-Security-Policy"]


def test_request_bodies_are_size_limited(user):
    r = user.post("/api/projects", json={"name": "x" * 70000})
    assert r.status_code == 413 and r.is_json


# ---------------------------------------------------------------- projects


def test_create_project_normalises_input(user):
    r = create_project(user, website_url="Example.ORG/shop/", keywords=" Plumber  Malmö,boiler repair,PLUMBER MALMÖ ,")
    assert r.status_code == 201
    p = r.get_json()["project"]
    assert p["website_url"] == "https://example.org/shop" and p["domain"] == "example.org"
    assert p["keywords"] == ["plumber malmö", "boiler repair"]
    assert p["location_name"] == "Sweden" and p["language_code"] == "sv"


@pytest.mark.parametrize(
    "overrides",
    [
        {"name": ""},
        {"website_url": "ftp://example.org"},
        {"website_url": "https://user:pw@example.org"},
        {"website_url": "https://example.org:8080"},
        {"website_url": "http://localhost"},
        {"website_url": "http://127.0.0.1"},
        {"website_url": "javascript:alert(1)"},
        {"website_url": "not a url"},
        {"keywords": ""},
        {"keywords": []},
        {"keywords": [1, 2]},
        {"keywords": "a" * 81},
        {"keywords": "one two three four five six seven eight nine ten eleven"},
        {"keywords": "<script>alert(1)</script>"},
        {"location_name": "Sweden; DROP TABLE"},
        {"language_code": "swedish"},
    ],
)
def test_create_project_rejects_bad_input(user, overrides):
    r = create_project(user, **overrides)
    assert r.status_code == 400, overrides
    assert r.get_json()["code"] == "validation_error"


def test_keyword_limit_follows_the_plan(make_client):
    c = make_client()
    register(c, plan="starter")
    ten = ",".join(f"keyword {i}" for i in range(PLANS["starter"]))
    assert create_project(c, keywords=ten).status_code == 201
    eleven = ten + ",keyword extra"
    r = create_project(c, keywords=eleven)
    assert r.status_code == 400 and "up to 10" in r.get_json()["error"]
    pro = make_client()
    register(pro, email="pro@example.com", plan="professional")
    assert create_project(pro, keywords=eleven).status_code == 201


def test_project_limit(app, user):
    app.config["MAX_PROJECTS_PER_USER"] = 2
    assert create_project(user).status_code == 201
    assert create_project(user).status_code == 201
    r = create_project(user)
    assert r.status_code == 409 and r.get_json()["code"] == "project_limit"


def test_update_and_delete_project(user):
    pid = create_project(user).get_json()["project"]["id"]
    r = user.patch(f"/api/projects/{pid}", json={"name": "Renamed", "keywords": ["boiler repair", "new term"]})
    assert r.status_code == 200
    assert r.get_json()["project"]["keywords"] == ["boiler repair", "new term"]  # 'boiler repair' kept, 'new term' added
    user.post(f"/api/projects/{pid}/analyze")
    user.post(f"/api/projects/{pid}/reports")
    assert user.delete(f"/api/projects/{pid}").status_code == 204
    assert user.get(f"/api/projects/{pid}").status_code == 404
    assert user.get("/api/projects").get_json() == {"projects": []}


# ---------------------------------------------------------------- analysis: sample data end to end


def test_analysis_without_credentials_is_labelled_sample_data(user):
    pid = create_project(user).get_json()["project"]["id"]
    r = user.post(f"/api/projects/{pid}/analyze")
    assert r.status_code == 201
    analysis = r.get_json()["analysis"]
    assert analysis["is_sample"] is True and analysis["provider"] == "sample"
    result = analysis["result"]
    assert result["is_sample"] is True and result["data_label"].startswith("SAMPLE DATA")
    assert [k["keyword"] for k in result["keywords"]] == ["plumber malmö", "emergency plumbing", "boiler repair"]
    assert all(k["search_volume"] and k["difficulty"] for k in result["keywords"])
    assert result["competitors"] and all(c["domain"].endswith(".example") for c in result["competitors"])
    assert result["technical_audit"]["available"] is True


def test_dashboard_carries_the_sample_flag_stats_and_reports(user):
    pid = create_project(user).get_json()["project"]["id"]
    empty = user.get(f"/api/projects/{pid}/dashboard").get_json()
    assert empty["latest_analysis"] is None and empty["stats"] is None
    assert empty["data_source"]["is_sample"] is True  # what the next analysis will use
    user.post(f"/api/projects/{pid}/analyze")
    user.post(f"/api/projects/{pid}/reports")
    d = user.get(f"/api/projects/{pid}/dashboard").get_json()
    assert d["data_source"] == {"provider": "sample", "is_sample": True, "label": d["data_source"]["label"]}
    assert d["data_source"]["label"].startswith("SAMPLE DATA")
    stats = d["stats"]
    assert stats["keywords_tracked"] == 3
    assert stats["in_top_10"] <= 3 and stats["not_found"] + stats["in_top_10"] <= 3
    assert len(d["reports"]) == 1 and d["reports"][0]["is_sample"] is True
    assert d["project"]["last_analyzed_at"]


def test_a_second_run_compares_with_the_first_of_the_same_kind(user):
    pid = create_project(user).get_json()["project"]["id"]
    first = user.post(f"/api/projects/{pid}/analyze").get_json()["analysis"]["result"]
    second = user.post(f"/api/projects/{pid}/analyze").get_json()["analysis"]["result"]
    assert all(k["previous_rank"] is None for k in first["keywords"])
    assert [k["previous_rank"] for k in second["keywords"]] == [k["rank"] for k in first["keywords"]]
    latest = user.get(f"/api/projects/{pid}/analyses/latest").get_json()["analysis"]
    assert latest["result"]["keywords"] == second["keywords"]


def test_latest_analysis_404_before_any_run(user):
    pid = create_project(user).get_json()["project"]["id"]
    assert user.get(f"/api/projects/{pid}/analyses/latest").status_code == 404


# ---------------------------------------------------------------- provider failures


class FailingProvider(SampleProvider):
    name = "dataforseo"
    is_sample = False

    def __init__(self, error):
        self.error = error

    def get_serp(self, *args, **kwargs):
        raise self.error


@pytest.mark.parametrize(
    "error, status, code",
    [
        (ProviderAuthError("rejected"), 502, "provider_auth_failed"),
        (ProviderPaymentError("balance"), 502, "provider_payment_required"),
        (ProviderRateLimitError("slow down", retry_after=30), 429, "provider_rate_limited"),
        (ProviderError("DataForSEO error 40501: Invalid Field."), 502, "provider_error"),
    ],
)
def test_provider_failures_become_clean_api_errors_and_store_nothing(app, user, error, status, code):
    pid = create_project(user).get_json()["project"]["id"]
    app.extensions["siktio_provider"] = FailingProvider(error)
    r = user.post(f"/api/projects/{pid}/analyze")
    assert r.status_code == status and r.get_json()["code"] == code
    assert user.get(f"/api/projects/{pid}/analyses/latest").status_code == 404


def test_unexpected_errors_do_not_leak_details(app, user):
    pid = create_project(user).get_json()["project"]["id"]
    app.extensions["siktio_provider"] = FailingProvider(RuntimeError("secret internal detail /etc/passwd"))
    r = user.post(f"/api/projects/{pid}/analyze")
    assert r.status_code == 500 and r.get_json()["code"] == "internal_error"
    assert "secret internal detail" not in r.get_data(as_text=True)


def test_real_data_is_not_labelled_sample(app, user):
    class Real(SampleProvider):
        name = "dataforseo"
        is_sample = False

    pid = create_project(user).get_json()["project"]["id"]
    app.extensions["siktio_provider"] = Real()
    analysis = user.post(f"/api/projects/{pid}/analyze").get_json()["analysis"]
    assert analysis["is_sample"] is False and analysis["provider"] == "dataforseo"
    assert not analysis["result"]["data_label"].startswith("SAMPLE")
    # And it is not compared with the earlier-sample/other-provider runs.
    again = user.post(f"/api/projects/{pid}/analyze").get_json()["analysis"]["result"]
    assert all(k["previous_rank"] == k["rank"] for k in again["keywords"])


# ---------------------------------------------------------------- reports


def test_report_needs_an_analysis_first(user):
    pid = create_project(user).get_json()["project"]["id"]
    r = user.post(f"/api/projects/{pid}/reports")
    assert r.status_code == 409 and r.get_json()["code"] == "no_analysis"


def test_template_report_end_to_end(user):
    pid = create_project(user).get_json()["project"]["id"]
    user.post(f"/api/projects/{pid}/analyze")
    r = user.post(f"/api/projects/{pid}/reports")
    assert r.status_code == 201
    report = r.get_json()["report"]
    assert report["generator"] == "template" and report["is_sample"] is True and report["model"] is None
    assert report["needs_human_review"] is True and report["reviewed_at"] is None
    content = report["content"]
    assert content["generated_by"]["kind"] == "template" and "not an AI analysis" in content["generated_by"]["note"]
    assert "person must review" in content["disclaimer"]
    assert content["data_source"]["label"].startswith("SAMPLE DATA")
    assert content["sections"]["executive_summary"].startswith("SAMPLE DATA")
    assert user.get(f"/api/reports/{report['id']}").get_json()["report"]["content"] == content
    assert [x["id"] for x in user.get(f"/api/projects/{pid}/reports").get_json()["reports"]] == [report["id"]]


def test_marking_a_report_reviewed(user):
    pid = create_project(user).get_json()["project"]["id"]
    user.post(f"/api/projects/{pid}/analyze")
    rid = user.post(f"/api/projects/{pid}/reports").get_json()["report"]["id"]
    r = user.post(f"/api/reports/{rid}/review").get_json()["report"]
    assert r["reviewed_at"] and r["needs_human_review"] is False
    again = user.post(f"/api/reports/{rid}/review").get_json()["report"]
    assert again["reviewed_at"] == r["reviewed_at"]  # idempotent
    assert user.delete(f"/api/reports/{rid}").status_code == 204


def test_report_uses_the_injected_model_function_when_a_key_is_configured():
    calls = []

    def fake_llm(messages, *, api_key, model, timeout):
        calls.append((api_key, model))
        return json.dumps(LLM_REPLY)

    app = create_app(make_env(OPENAI_API_KEY="sk-test", OPENAI_MODEL="test-model"), llm=fake_llm)
    c = new_client(app)
    register(c)
    pid = create_project(c).get_json()["project"]["id"]
    c.post(f"/api/projects/{pid}/analyze")
    report = c.post(f"/api/projects/{pid}/reports").get_json()["report"]
    assert calls == [("sk-test", "test-model")]
    assert report["generator"] == "openai" and report["model"] == "test-model"
    assert report["content"]["sections"]["executive_summary"] == "Summary."
    assert "person must review" in report["content"]["disclaimer"]  # still attached
    assert report["content"]["data_source"]["is_sample"] is True  # AI text does not remove the sample flag
    assert "sk-test" not in json.dumps(report)


def test_report_falls_back_to_template_when_the_model_fails():
    def broken_llm(messages, *, api_key, model, timeout):
        from src.reports import LLMError

        raise LLMError("OpenAI request failed (APIConnectionError).")

    app = create_app(make_env(OPENAI_API_KEY="sk-test"), llm=broken_llm)
    c = new_client(app)
    register(c)
    pid = create_project(c).get_json()["project"]["id"]
    c.post(f"/api/projects/{pid}/analyze")
    report = c.post(f"/api/projects/{pid}/reports").get_json()["report"]
    assert report["generator"] == "template"
    assert "request failed" in report["content"]["fallback_reason"]


def test_report_for_a_chosen_analysis(user):
    pid = create_project(user).get_json()["project"]["id"]
    first = user.post(f"/api/projects/{pid}/analyze").get_json()["analysis"]["id"]
    user.post(f"/api/projects/{pid}/analyze")
    r = user.post(f"/api/projects/{pid}/reports", json={"analysis_id": first})
    assert r.get_json()["report"]["analysis_id"] == first
    assert user.post(f"/api/projects/{pid}/reports", json={"analysis_id": "x"}).status_code == 400
    assert user.post(f"/api/projects/{pid}/reports", json={"analysis_id": 99999}).status_code == 404


# ---------------------------------------------------------------- static front end


def test_root_explains_when_the_frontend_is_not_built(tmp_path):
    c = new_client(create_app(make_env(STATIC_DIR=str(tmp_path))))  # an empty folder: no index.html
    r = c.get("/")
    assert r.status_code == 200 and "npm run build" in r.get_data(as_text=True)


def test_spa_fallback_and_path_traversal(tmp_path):
    (tmp_path / "index.html").write_text("<!doctype html><title>spa</title>")
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "app.js").write_text("console.log(1)")
    secret = tmp_path.parent / "outside.txt"
    secret.write_text("TOP SECRET")
    app = create_app(make_env(STATIC_DIR=str(tmp_path)))
    c = new_client(app)
    assert "spa" in c.get("/dashboard/3").get_data(as_text=True)
    assert c.get("/assets/app.js").get_data(as_text=True) == "console.log(1)"
    for path in ["/../outside.txt", "/%2e%2e/outside.txt", "/assets/../../outside.txt"]:
        assert "TOP SECRET" not in c.get(path).get_data(as_text=True)
    assert c.get("/api/does-not-exist").is_json
