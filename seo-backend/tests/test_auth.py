import re

from src.extensions import db
from src.models import User

from .conftest import PASSWORD, new_client, register


def test_register_logs_in_and_hashes_the_password(app, client):
    response = register(client, email="Owner@Example.com")
    assert response.status_code == 201
    body = response.get_json()
    assert body["user"]["email"] == "owner@example.com"
    assert "password" not in body["user"] and "password_hash" not in body["user"]
    assert client.get("/api/auth/me").get_json()["user"]["email"] == "owner@example.com"
    with app.app_context():
        stored = User.query.one().password_hash
    assert PASSWORD not in stored
    assert re.match(r"^(scrypt|pbkdf2):", stored)


def test_password_hashes_are_salted(app, make_client):
    register(make_client(), email="a@example.com")
    register(make_client(), email="b@example.com")
    with app.app_context():
        a, b = [u.password_hash for u in User.query.order_by(User.id)]
    assert a != b


def test_cookie_flags(client):
    response = register(client)
    cookie = response.headers["Set-Cookie"]
    assert "HttpOnly" in cookie and "SameSite=Lax" in cookie
    assert "siktio_session=" in cookie


def test_login_logout_roundtrip(make_client, user):
    other = make_client()
    assert other.post("/api/auth/login", json={"email": "owner@example.com", "password": PASSWORD}).status_code == 200
    assert other.get("/api/auth/me").status_code == 200
    assert other.post("/api/auth/logout").status_code == 200
    assert other.get("/api/auth/me").status_code == 401


def test_wrong_password_and_unknown_email_look_the_same(make_client, user):
    c = make_client()
    wrong = c.post("/api/auth/login", json={"email": "owner@example.com", "password": "not the password"})
    unknown = c.post("/api/auth/login", json={"email": "nobody@example.com", "password": "not the password"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.get_json() == unknown.get_json()


def test_login_is_throttled_after_repeated_failures(make_client, user):
    c = make_client()
    for _ in range(5):
        assert c.post("/api/auth/login", json={"email": "owner@example.com", "password": "bad bad bad bad"}).status_code == 401
    blocked = c.post("/api/auth/login", json={"email": "owner@example.com", "password": PASSWORD})
    assert blocked.status_code == 429  # even the right password is refused while blocked


def test_successful_login_resets_the_failure_count(make_client, user):
    c = make_client()
    for _ in range(3):
        c.post("/api/auth/login", json={"email": "owner@example.com", "password": "bad bad bad bad"})
    assert c.post("/api/auth/login", json={"email": "owner@example.com", "password": PASSWORD}).status_code == 200
    for _ in range(3):
        assert c.post("/api/auth/login", json={"email": "owner@example.com", "password": "bad bad bad bad"}).status_code == 401


def test_registration_validation(client):
    assert register(client, email="not-an-email").status_code == 400
    assert register(client, password="short").status_code == 400
    assert register(client, password="x" * 129).status_code == 400
    assert register(client, password="          ").status_code == 400
    assert register(client, plan="gold").status_code == 400
    assert client.post("/api/auth/register", json=["nope"]).status_code == 400
    assert client.post("/api/auth/register", data="email=a", headers={"Content-Type": "text/plain"}).status_code == 400


def test_duplicate_email_is_rejected_case_insensitively(user, make_client):
    assert register(make_client(), email="OWNER@example.com").status_code == 409


def test_registration_can_be_closed(app):
    app.config["ALLOW_REGISTRATION"] = False
    assert register(new_client(app)).status_code == 403


def test_plan_is_validated_and_stored(app, client):
    body = register(client, plan="Professional").get_json()
    assert body["user"]["plan"] == "professional"


def test_state_changing_requests_need_the_client_header(app):
    bare = app.test_client()  # no X-Requested-With
    response = bare.post("/api/auth/register", json={"email": "a@example.com", "password": PASSWORD})
    assert response.status_code == 403 and response.get_json()["code"] == "csrf"
    assert bare.get("/api/health").status_code == 200  # reads do not need it


def test_protected_routes_reject_anonymous_requests(client):
    for method, path in [
        ("get", "/api/auth/me"),
        ("get", "/api/projects"),
        ("post", "/api/projects"),
        ("get", "/api/projects/1"),
        ("post", "/api/projects/1/analyze"),
        ("get", "/api/reports/1"),
    ]:
        assert getattr(client, method)(path).status_code == 401, (method, path)


def test_a_deleted_user_loses_the_session(app, user):
    with app.app_context():
        db.session.delete(User.query.one())
        db.session.commit()
    assert user.get("/api/auth/me").status_code == 401


def test_responses_never_contain_secrets(app, user):
    body = user.get("/api/auth/me").get_data(as_text=True) + user.get("/api/health").get_data(as_text=True)
    assert app.config["SECRET_KEY"] not in body and "password" not in body.lower()


def test_signups_are_throttled_per_address(make_client):
    from src.app import create_app

    from .conftest import make_env

    app = create_app(make_env(REGISTER_MAX_PER_HOUR="3"))
    client = new_client(app)
    statuses = [register(client, email=f"user{i}@example.com").status_code for i in range(5)]
    assert statuses == [201, 201, 201, 429, 429]
