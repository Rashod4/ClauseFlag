import json
import os
import sqlite3
import sys
import time
import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from main import app, create_access_token, decode_access_token, DB_PATH  # noqa: E402

MOCK_TOS_TEXT = (
    "We collect your email address to provide our services. "
    "We may share your data with third-party advertising partners. "
    "You agree to binding arbitration for any disputes. "
    "We use cookies to track your browsing activity. "
    "You may delete your account at any time."
)


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def _register(client, username="testuser", password="secret123"):
    return client.post(
        "/api/register", json={"username": username, "password": password}
    )


def _auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── /api/register ───────────────────────────────────────────────────


def test_register_success(client):
    name = f"user_{uuid.uuid4().hex[:8]}"
    res = _register(client, username=name)
    assert res.status_code == 200
    body = res.json()
    assert "token" in body
    assert body["username"] == name
    assert "user_id" in body


def test_register_duplicate_username(client):
    name = f"dup_{uuid.uuid4().hex[:8]}"
    _register(client, username=name)
    res = _register(client, username=name)
    assert res.status_code == 409
    assert "already taken" in res.json()["detail"]


def test_register_short_username(client):
    res = _register(client, username="ab", password="secret123")
    assert res.status_code == 400
    assert "3 characters" in res.json()["detail"]


def test_register_short_password(client):
    name = f"user_{uuid.uuid4().hex[:8]}"
    res = _register(client, username=name, password="12345")
    assert res.status_code == 400
    assert "6 characters" in res.json()["detail"]


# ── /api/login ──────────────────────────────────────────────────────


def test_login_success(client):
    name = f"login_{uuid.uuid4().hex[:8]}"
    _register(client, username=name, password="mypassword")
    res = client.post("/api/login", json={"username": name, "password": "mypassword"})
    assert res.status_code == 200
    body = res.json()
    assert "token" in body
    assert body["username"] == name


def test_login_wrong_password(client):
    name = f"login_{uuid.uuid4().hex[:8]}"
    _register(client, username=name, password="correctpw")
    res = client.post("/api/login", json={"username": name, "password": "wrongpw"})
    assert res.status_code == 401


def test_login_nonexistent_user(client):
    res = client.post(
        "/api/login", json={"username": "ghost", "password": "nope1234"}
    )
    assert res.status_code == 401


# ── JWT helpers ─────────────────────────────────────────────────────


def test_jwt_round_trip():
    uid = str(uuid.uuid4())
    token = create_access_token(uid)
    assert decode_access_token(token) == uid


def test_jwt_invalid_token():
    assert decode_access_token("garbage.token.value") is None


# ── /api/history ────────────────────────────────────────────────────


def test_history_requires_auth(client):
    res = client.get("/api/history")
    assert res.status_code == 401


def test_history_rejects_bad_token(client):
    res = client.get("/api/history", headers=_auth_header("invalid.jwt.token"))
    assert res.status_code == 401


def test_history_empty_for_new_user(client):
    name = f"hist_{uuid.uuid4().hex[:8]}"
    reg = _register(client, username=name).json()
    res = client.get("/api/history", headers=_auth_header(reg["token"]))
    assert res.status_code == 200
    assert res.json()["history"] == []


def test_history_returns_saved_entries(client):
    name = f"hist_{uuid.uuid4().hex[:8]}"
    reg = _register(client, username=name).json()
    user_id = reg["user_id"]

    result_json = json.dumps({"analysis_id": "a1", "clause_count": 3, "risk_summary": {"safe": 2, "watch": 1, "danger": 0}})
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO history (id, user_id, url, analysis_result) VALUES (?, ?, ?, ?)",
        (str(uuid.uuid4()), user_id, "https://example.com/tos", result_json),
    )
    conn.commit()
    conn.close()

    res = client.get("/api/history", headers=_auth_header(reg["token"]))
    assert res.status_code == 200
    items = res.json()["history"]
    assert len(items) == 1
    assert items[0]["url"] == "https://example.com/tos"
    assert items[0]["analysis_result"]["clause_count"] == 3


# ── /api/analyze with auth → history ────────────────────────────────


def _poll_until_complete(client, analysis_id: str, max_attempts: int = 120):
    for _ in range(max_attempts):
        res = client.get(f"/api/analyses/{analysis_id}")
        assert res.status_code == 200
        data = res.json()
        if data["status"] in ("complete", "failed"):
            return data
        time.sleep(0.5)
    raise TimeoutError("Analysis did not complete in time")


@patch("scraper.scrape_url", return_value=MOCK_TOS_TEXT)
def test_analyze_with_auth_saves_history(mock_scrape, client):
    name = f"authhist_{uuid.uuid4().hex[:8]}"
    reg = _register(client, username=name).json()
    token = reg["token"]

    unique_url = f"https://example.com/tos/{uuid.uuid4()}"
    res = client.post(
        "/api/analyze",
        json={"url": unique_url},
        headers=_auth_header(token),
    )
    assert res.status_code == 200
    analysis_id = res.json()["id"]

    _poll_until_complete(client, analysis_id)

    history_res = client.get("/api/history", headers=_auth_header(token))
    items = history_res.json()["history"]
    assert len(items) == 1
    assert items[0]["url"] == unique_url
    assert items[0]["analysis_result"]["analysis_id"] == analysis_id


def test_analyze_without_auth_no_history(client):
    text = (
        "We may share your personal data with third-party advertising partners. "
        "You agree to binding arbitration for any disputes that arise from use of this service."
    )
    res = client.post("/api/analyze", json={"text": text})
    assert res.status_code == 200
    analysis_id = res.json()["id"]

    _poll_until_complete(client, analysis_id)

    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT COUNT(*) FROM history WHERE url IS NULL AND analysis_result LIKE ?",
        (f'%{analysis_id}%',),
    ).fetchone()
    conn.close()
    assert row[0] == 0
