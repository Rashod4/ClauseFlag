"""Endpoint-level tests for auth and history, with mocked internals."""

import json
import os
import sys
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from main import (  # noqa: E402
    app,
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    JWT_SECRET,
    JWT_ALGORITHM,
)

import jwt as pyjwt  # noqa: E402


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def _register(client, username=None, password="secret123"):
    username = username or f"u_{uuid.uuid4().hex[:8]}"
    return client.post(
        "/api/register", json={"username": username, "password": password}
    )


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Password hashing ───────────────────────────────────────────────


def test_hash_password_produces_bcrypt_string():
    h = hash_password("mypassword")
    assert h.startswith("$2")
    assert len(h) >= 59


def test_verify_password_correct():
    h = hash_password("hunter2")
    assert verify_password("hunter2", h) is True


def test_verify_password_wrong():
    h = hash_password("correct")
    assert verify_password("wrong", h) is False


def test_hash_is_unique_per_call():
    a = hash_password("same")
    b = hash_password("same")
    assert a != b


# ── JWT edge cases ──────────────────────────────────────────────────


def test_expired_token_returns_none():
    payload = {
        "sub": "user-123",
        "exp": datetime.utcnow() - timedelta(hours=1),
    }
    token = pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    assert decode_access_token(token) is None


def test_token_with_wrong_secret_returns_none():
    payload = {
        "sub": "user-123",
        "exp": datetime.utcnow() + timedelta(hours=1),
    }
    token = pyjwt.encode(payload, "wrong-secret-key-definitely!", algorithm=JWT_ALGORITHM)
    assert decode_access_token(token) is None


def test_token_missing_sub_returns_none():
    payload = {"exp": datetime.utcnow() + timedelta(hours=1)}
    token = pyjwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    assert decode_access_token(token) is None


# ── Register endpoint edge cases ───────────────────────────────────


def test_register_returns_usable_token(client):
    res = _register(client)
    token = res.json()["token"]
    history_res = client.get("/api/history", headers=_auth(token))
    assert history_res.status_code == 200


def test_register_token_contains_correct_user_id(client):
    res = _register(client).json()
    decoded_uid = decode_access_token(res["token"])
    assert decoded_uid == res["user_id"]


def test_register_missing_fields(client):
    res = client.post("/api/register", json={"username": "onlyuser"})
    assert res.status_code == 422


def test_register_empty_body(client):
    res = client.post("/api/register", json={})
    assert res.status_code == 422


# ── Login endpoint edge cases ──────────────────────────────────────


def test_login_token_contains_same_user_id_as_register(client):
    name = f"lid_{uuid.uuid4().hex[:8]}"
    reg = _register(client, username=name, password="pass123456").json()

    login_res = client.post(
        "/api/login", json={"username": name, "password": "pass123456"}
    )
    login_data = login_res.json()

    assert login_data["user_id"] == reg["user_id"]
    assert decode_access_token(login_data["token"]) == reg["user_id"]


def test_login_missing_password(client):
    res = client.post("/api/login", json={"username": "someone"})
    assert res.status_code == 422


# ── History isolation between users ─────────────────────────────────


def test_history_is_isolated_between_users(client):
    user_a = _register(client).json()
    user_b = _register(client).json()

    from main import DB_PATH
    import sqlite3

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO history (id, user_id, url, analysis_result) VALUES (?, ?, ?, ?)",
        (str(uuid.uuid4()), user_a["user_id"], "https://a.com", '{"x":1}'),
    )
    conn.commit()
    conn.close()

    res_a = client.get("/api/history", headers=_auth(user_a["token"]))
    res_b = client.get("/api/history", headers=_auth(user_b["token"]))

    assert len(res_a.json()["history"]) == 1
    assert len(res_b.json()["history"]) == 0


def test_history_ordered_newest_first(client):
    reg = _register(client).json()

    from main import DB_PATH
    import sqlite3

    conn = sqlite3.connect(DB_PATH)
    for i, ts in enumerate(["2025-01-01 00:00:00", "2025-06-01 00:00:00"]):
        conn.execute(
            "INSERT INTO history (id, user_id, url, analysis_result, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (str(uuid.uuid4()), reg["user_id"], f"https://ex.com/{i}", '{}', ts),
        )
    conn.commit()
    conn.close()

    res = client.get("/api/history", headers=_auth(reg["token"]))
    items = res.json()["history"]
    assert len(items) == 2
    assert items[0]["url"] == "https://ex.com/1"


def test_history_null_analysis_result_returns_none(client):
    reg = _register(client).json()

    from main import DB_PATH
    import sqlite3

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO history (id, user_id, url, analysis_result) VALUES (?, ?, ?, ?)",
        (str(uuid.uuid4()), reg["user_id"], "https://ex.com", None),
    )
    conn.commit()
    conn.close()

    res = client.get("/api/history", headers=_auth(reg["token"]))
    item = res.json()["history"][0]
    assert item["analysis_result"] is None


# ── _parse_clause_row backward compat ───────────────────────────────


def test_parse_clause_row_handles_legacy_plain_string():
    from main import _parse_clause_row

    class FakeRow:
        def __init__(self, d):
            self._d = d

        def keys(self):
            return self._d.keys()

        def __getitem__(self, k):
            return self._d[k]

    row = FakeRow({"explanation": "Old plain string explanation"})
    parsed = _parse_clause_row(row)
    assert parsed["explanation"]["summary"] == "Old plain string explanation"
    assert parsed["explanation"]["unusual"] == ""
    assert parsed["explanation"]["risks"] == ""


def test_parse_clause_row_handles_valid_json():
    from main import _parse_clause_row

    class FakeRow:
        def __init__(self, d):
            self._d = d

        def keys(self):
            return self._d.keys()

        def __getitem__(self, k):
            return self._d[k]

    payload = {"summary": "S", "unusual": "U", "risks": "R"}
    row = FakeRow({"explanation": json.dumps(payload)})
    parsed = _parse_clause_row(row)
    assert parsed["explanation"] == payload
