"""Shared fixtures. Nothing here touches the network or the process environment:
`create_app({...})` reads only the mapping it is given."""
from __future__ import annotations

import json

import pytest
import requests

from src.app import CLIENT_HEADER, CLIENT_HEADER_VALUE, create_app

PASSWORD = "correct horse battery"


def make_env(**overrides: str) -> dict[str, str]:
    env = {
        "APP_ENV": "testing",
        "SECRET_KEY": "test-secret-key-that-is-long-enough-0123456789",
        "DATABASE_URL": "sqlite://",
        "LOGIN_MAX_FAILURES": "5",
    }
    env.update(overrides)
    return env


@pytest.fixture
def app():
    return create_app(make_env())


def new_client(app):
    client = app.test_client()
    client.environ_base["HTTP_" + CLIENT_HEADER.upper().replace("-", "_")] = CLIENT_HEADER_VALUE
    return client


@pytest.fixture
def client(app):
    return new_client(app)


@pytest.fixture
def make_client(app):
    return lambda: new_client(app)


def register(client, email="owner@example.com", password=PASSWORD, **extra):
    return client.post("/api/auth/register", json={"email": email, "password": password, **extra})


@pytest.fixture
def user(client):
    response = register(client)
    assert response.status_code == 201, response.get_json()
    return client


def create_project(client, **overrides):
    body = {
        "name": "Main site",
        "website_url": "https://www.example.org",
        "keywords": "plumber malmö, emergency plumbing, boiler repair",
    }
    body.update(overrides)
    return client.post("/api/projects", json=body)


# ---------------------------------------------------------------- fake HTTP layer for DataForSEO


def make_response(status=200, body=None, headers=None, text=None):
    response = requests.Response()
    response.status_code = status
    response._content = (text if text is not None else json.dumps(body if body is not None else {})).encode("utf-8")
    response.headers.update(headers or {})
    response.encoding = "utf-8"
    return response


class FakeAdapter(requests.adapters.BaseAdapter):
    """Plays back queued responses (or exceptions) and records every request."""

    def __init__(self, *queue):
        super().__init__()
        self.queue = list(queue)
        self.requests: list[requests.PreparedRequest] = []

    def send(self, request, **kwargs):
        self.requests.append(request)
        item = self.queue.pop(0) if len(self.queue) > 1 else self.queue[0]
        if isinstance(item, Exception):
            raise item
        item.request = request
        item.url = request.url
        return item

    def close(self):
        pass


def session_with(*queue):
    session = requests.Session()
    adapter = FakeAdapter(*queue)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session, adapter


def api_ok(result, *, path="serp/google/organic/live/advanced", status_code=20000):
    return {
        "version": "0.1.20240801",
        "status_code": 20000,
        "status_message": "Ok.",
        "tasks_count": 1,
        "tasks_error": 0,
        "tasks": [
            {
                "id": "00000000-0000-0000-0000-000000000000",
                "status_code": status_code,
                "status_message": "Ok.",
                "path": path.split("/"),
                "result": result,
            }
        ],
    }
