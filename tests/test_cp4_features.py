"""Tests for Checkpoint 4 features: unusual clause detection, sorting, and DB indexes."""

import os
import sys
import time
import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from main import app, ANOMALY_THRESHOLD  # noqa: E402

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


def _poll_until_complete(client, analysis_id: str, max_attempts: int = 120):
    for _ in range(max_attempts):
        res = client.get(f"/api/analyses/{analysis_id}")
        assert res.status_code == 200
        data = res.json()
        if data["status"] in ("complete", "failed"):
            return data
        time.sleep(0.5)
    raise TimeoutError("Analysis did not complete in time")


def _run_analysis(client, text=None):
    """Helper to submit text and wait for completion."""
    payload = {"text": text or MOCK_TOS_TEXT}
    res = client.post("/api/analyze", json=payload)
    assert res.status_code == 200
    body = res.json()
    analysis = _poll_until_complete(client, body["id"])
    assert analysis["status"] == "complete"
    return body["id"], analysis


# ---------------------------------------------------------------------------
# Unusual clause detection
# ---------------------------------------------------------------------------

def test_risk_summary_includes_unusual_count(client):
    """The risk_summary should contain an 'unusual' count."""
    analysis_id, analysis = _run_analysis(client)
    assert "unusual" in analysis["risk_summary"]
    assert isinstance(analysis["risk_summary"]["unusual"], int)
    assert analysis["risk_summary"]["unusual"] >= 0


def test_anomaly_threshold_is_applied(client):
    """Unusual count should match clauses with anomaly_score >= threshold."""
    analysis_id, analysis = _run_analysis(client)

    res = client.get(f"/api/analyses/{analysis_id}/clauses")
    clauses = res.json()["clauses"]

    manual_unusual = sum(
        1 for c in clauses if c["anomaly_score"] >= ANOMALY_THRESHOLD
    )
    assert analysis["risk_summary"]["unusual"] == manual_unusual


# ---------------------------------------------------------------------------
# Sorting
# ---------------------------------------------------------------------------

def test_sort_by_anomaly(client):
    """Clauses sorted by anomaly should be in descending anomaly_score order."""
    analysis_id, _ = _run_analysis(client)

    res = client.get(f"/api/analyses/{analysis_id}/clauses?sort=anomaly")
    assert res.status_code == 200
    clauses = res.json()["clauses"]

    scores = [c["anomaly_score"] for c in clauses]
    assert scores == sorted(scores, reverse=True)


def test_sort_by_confidence(client):
    """Clauses sorted by confidence should be in descending confidence order."""
    analysis_id, _ = _run_analysis(client)

    res = client.get(f"/api/analyses/{analysis_id}/clauses?sort=confidence")
    assert res.status_code == 200
    clauses = res.json()["clauses"]

    scores = [c["confidence"] for c in clauses]
    assert scores == sorted(scores, reverse=True)


def test_sort_by_risk(client):
    """Risk-priority sort should put danger first, then watch, then safe."""
    analysis_id, _ = _run_analysis(client)

    res = client.get(f"/api/analyses/{analysis_id}/clauses?sort=risk")
    assert res.status_code == 200
    clauses = res.json()["clauses"]

    risk_order = {"danger": 0, "watch": 1, "safe": 2}
    risk_values = [risk_order[c["risk"]] for c in clauses]
    assert risk_values == sorted(risk_values)


def test_sort_default_is_position(client):
    """Default sort should return clauses in document order (position ASC)."""
    analysis_id, _ = _run_analysis(client)

    res = client.get(f"/api/analyses/{analysis_id}/clauses")
    assert res.status_code == 200
    clauses = res.json()["clauses"]

    positions = [c["position"] for c in clauses]
    assert positions == sorted(positions)


def test_invalid_sort_falls_back_to_position(client):
    """An unrecognized sort value should fall back to position order."""
    analysis_id, _ = _run_analysis(client)

    res = client.get(f"/api/analyses/{analysis_id}/clauses?sort=invalid")
    assert res.status_code == 200
    clauses = res.json()["clauses"]

    positions = [c["position"] for c in clauses]
    assert positions == sorted(positions)


# ---------------------------------------------------------------------------
# DB indexes (verify they exist without errors)
# ---------------------------------------------------------------------------

def test_db_indexes_created(client):
    """DB indexes for performance should exist."""
    import sqlite3
    from main import DB_PATH

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    rows = c.execute(
        "SELECT name FROM sqlite_master WHERE type='index'"
    ).fetchall()
    conn.close()

    index_names = {row[0] for row in rows}
    assert "idx_analyses_url_status" in index_names
    assert "idx_clauses_analysis_id" in index_names
