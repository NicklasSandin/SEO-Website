"""One user must never see or change another user's projects, analyses or reports."""
import pytest

from .conftest import create_project, register


@pytest.fixture
def two_users(make_client):
    alice, bob = make_client(), make_client()
    assert register(alice, email="alice@example.com").status_code == 201
    assert register(bob, email="bob@example.com").status_code == 201
    project = create_project(alice, name="Alice's site").get_json()["project"]
    analysis = alice.post(f"/api/projects/{project['id']}/analyze").get_json()["analysis"]
    report = alice.post(f"/api/projects/{project['id']}/reports").get_json()["report"]
    return alice, bob, project["id"], analysis["id"], report["id"]


def test_the_owner_can_use_everything(two_users):
    alice, _, pid, _, rid = two_users
    assert alice.get(f"/api/projects/{pid}").status_code == 200
    assert alice.get(f"/api/projects/{pid}/dashboard").status_code == 200
    assert alice.get(f"/api/reports/{rid}").status_code == 200


def test_other_users_get_404_on_every_project_and_report_route(two_users):
    _, bob, pid, aid, rid = two_users
    checks = [
        ("get", f"/api/projects/{pid}", None),
        ("patch", f"/api/projects/{pid}", {"name": "hijacked"}),
        ("delete", f"/api/projects/{pid}", None),
        ("post", f"/api/projects/{pid}/analyze", None),
        ("get", f"/api/projects/{pid}/analyses/latest", None),
        ("get", f"/api/projects/{pid}/dashboard", None),
        ("get", f"/api/projects/{pid}/reports", None),
        ("post", f"/api/projects/{pid}/reports", None),
        ("get", f"/api/reports/{rid}", None),
        ("post", f"/api/reports/{rid}/review", None),
        ("delete", f"/api/reports/{rid}", None),
    ]
    for method, path, body in checks:
        response = getattr(bob, method)(path, **({"json": body} if body else {}))
        assert response.status_code == 404, (method, path, response.status_code)
        assert "Alice" not in response.get_data(as_text=True)


def test_other_users_lists_are_empty_and_ids_do_not_leak(two_users):
    alice, bob, pid, *_ = two_users
    assert bob.get("/api/projects").get_json() == {"projects": []}
    assert [p["id"] for p in alice.get("/api/projects").get_json()["projects"]] == [pid]


def test_a_user_cannot_build_a_report_from_someone_elses_analysis(two_users):
    _, bob, pid, aid, _ = two_users
    own = create_project(bob, name="Bob's site").get_json()["project"]
    bob.post(f"/api/projects/{own['id']}/analyze")
    response = bob.post(f"/api/projects/{own['id']}/reports", json={"analysis_id": aid})
    assert response.status_code == 404


def test_failed_attempts_changed_nothing(two_users):
    alice, bob, pid, _, rid = two_users
    bob.patch(f"/api/projects/{pid}", json={"name": "hijacked"})
    bob.delete(f"/api/projects/{pid}")
    bob.post(f"/api/reports/{rid}/review")
    project = alice.get(f"/api/projects/{pid}").get_json()["project"]
    assert project["name"] == "Alice's site"
    assert alice.get(f"/api/reports/{rid}").get_json()["report"]["reviewed_at"] is None


def test_the_daily_analysis_quota_is_per_user(app, make_client):
    app.config["MAX_ANALYSES_PER_USER_PER_DAY"] = 1
    alice, bob = make_client(), make_client()
    register(alice, email="alice@example.com")
    register(bob, email="bob@example.com")
    pa = create_project(alice).get_json()["project"]["id"]
    pb = create_project(bob).get_json()["project"]["id"]
    assert alice.post(f"/api/projects/{pa}/analyze").status_code == 201
    assert alice.post(f"/api/projects/{pa}/analyze").status_code == 429
    assert bob.post(f"/api/projects/{pb}/analyze").status_code == 201  # Alice's usage does not count against Bob
