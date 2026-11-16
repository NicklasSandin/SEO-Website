import pytest

from src.app import create_app
from src.config import ConfigError, load_config

from .conftest import make_env


def test_production_without_a_secret_key_fails_closed():
    with pytest.raises(ConfigError, match="SECRET_KEY"):
        load_config({"APP_ENV": "production"})
    with pytest.raises(ConfigError):
        create_app({"APP_ENV": "production", "DATABASE_URL": "sqlite://"})


@pytest.mark.parametrize("secret", ["short", "change-me", "x" * 31, "CHANGE-ME"])
def test_production_rejects_short_or_placeholder_secret_keys(secret):
    with pytest.raises(ConfigError):
        load_config({"APP_ENV": "production", "SECRET_KEY": secret})


def test_production_accepts_a_long_random_secret_and_sets_secure_cookies():
    config = load_config({"APP_ENV": "production", "SECRET_KEY": "a" * 40})
    assert config["SESSION_COOKIE_SECURE"] is True and config["APP_ENV"] == "production"


def test_development_without_a_secret_gets_a_random_per_process_key():
    a = load_config({"APP_ENV": "development"})["SECRET_KEY"]
    b = load_config({"APP_ENV": "development"})["SECRET_KEY"]
    assert a and b and a != b and len(a) >= 32


def test_default_environment_is_development_not_production():
    assert load_config({})["APP_ENV"] == "development"


def test_cors_is_closed_by_default_and_wildcard_is_refused():
    assert load_config({})["CORS_ORIGINS"] == ()
    assert load_config({"CORS_ORIGINS": "http://localhost:5173, https://app.example.org/"})["CORS_ORIGINS"] == (
        "http://localhost:5173",
        "https://app.example.org",
    )
    with pytest.raises(ConfigError):
        load_config({"CORS_ORIGINS": "*"})


def test_dataforseo_credentials_must_come_as_a_pair_and_provider_choice_is_checked():
    with pytest.raises(ConfigError):
        load_config({"DATAFORSEO_LOGIN": "a"})
    with pytest.raises(ConfigError):
        load_config({"RANK_PROVIDER": "dataforseo"})
    with pytest.raises(ConfigError):
        load_config({"RANK_PROVIDER": "nope"})
    with pytest.raises(ConfigError):
        load_config({"REPORT_GENERATOR": "openai"})


def test_provider_selection_follows_the_credentials():
    sample = create_app(make_env())
    assert sample.extensions["siktio_provider"].is_sample
    real = create_app(make_env(DATAFORSEO_LOGIN="l", DATAFORSEO_PASSWORD="p"))
    assert real.extensions["siktio_provider"].name == "dataforseo"
    forced = create_app(make_env(DATAFORSEO_LOGIN="l", DATAFORSEO_PASSWORD="p", RANK_PROVIDER="sample"))
    assert forced.extensions["siktio_provider"].is_sample


def test_numbers_are_validated():
    with pytest.raises(ConfigError):
        load_config({"SERP_DEPTH": "five"})
    with pytest.raises(ConfigError):
        load_config({"SERP_DEPTH": "5"})


def test_cors_headers_only_for_listed_origins():
    app = create_app(make_env(CORS_ORIGINS="https://app.example.org"))
    client = app.test_client()
    ok = client.get("/api/health", headers={"Origin": "https://app.example.org"})
    assert ok.headers["Access-Control-Allow-Origin"] == "https://app.example.org"
    assert ok.headers["Access-Control-Allow-Credentials"] == "true"
    other = client.get("/api/health", headers={"Origin": "https://evil.example"})
    assert "Access-Control-Allow-Origin" not in other.headers
    closed = create_app(make_env()).test_client().get("/api/health", headers={"Origin": "https://app.example.org"})
    assert "Access-Control-Allow-Origin" not in closed.headers


def test_sessions_signed_by_one_key_are_not_accepted_by_an_app_with_another_key():
    from .conftest import new_client, register

    a = create_app(make_env(SECRET_KEY="a" * 40))
    b = create_app(make_env(SECRET_KEY="b" * 40))
    ca = new_client(a)
    assert register(ca).status_code == 201
    cookie = ca.get_cookie("siktio_session")
    cb = new_client(b)
    cb.set_cookie("siktio_session", cookie.value)
    assert cb.get("/api/auth/me").status_code == 401
