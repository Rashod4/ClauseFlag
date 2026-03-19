import os
import sys
import time
import uuid
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from main import app  # noqa: E402

MOCK_TOS_TEXT = (
    "We collect your email address to provide our services. "
    "We may share your data with third-party advertising partners. "
    "You agree to binding arbitration for any disputes. "
    "We use cookies to track your browsing activity. "
    "You may delete your account at any time."
)

CLAUSE_FIELDS = {
    "id", "text", "risk", "confidence",
    "anomaly_score", "category", "explanation",
}


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


@patch("scraper.scrape_url", return_value=MOCK_TOS_TEXT)
def test_url_analysis_end_to_end(mock_scrape, client):
    unique_url = f"https://example.com/tos/{uuid.uuid4()}"
    res = client.post("/api/analyze", json={"url": unique_url})
    assert res.status_code == 200
    body = res.json()
    assert "id" in body
    assert body["status"] == "processing"

    analysis = _poll_until_complete(client, body["id"])
    assert analysis["status"] == "complete"
    assert analysis["clause_count"] > 0
    for key in ("safe", "watch", "danger"):
        assert key in analysis["risk_summary"]

    res = client.get(f"/api/analyses/{body['id']}/clauses")
    assert res.status_code == 200
    clauses = res.json()["clauses"]
    assert len(clauses) > 0
    for clause in clauses:
        assert CLAUSE_FIELDS <= set(clause.keys())
        assert clause["risk"] in ("safe", "watch", "danger")
        assert 0 <= clause["confidence"] <= 1
        assert 0 <= clause["anomaly_score"] <= 1

    mock_scrape.assert_called_once_with(unique_url)


@patch(
    "scraper.scrape_url",
    side_effect=ValueError(
        "Invalid URL scheme '': only http and https are supported"
    ),
)
def test_url_validation_rejects_bad_url(mock_scrape, client):
    res = client.post("/api/analyze", json={"url": "not-a-url"})
    assert res.status_code == 400
    assert "detail" in res.json()


def test_url_and_text_both_missing(client):
    res = client.post("/api/analyze", json={})
    assert res.status_code == 422


@patch(
    "scraper.scrape_url",
    side_effect=RuntimeError(
        "Network error while fetching 'https://down.example.com': ConnectionError"
    ),
)
def test_url_scrape_failure_returns_400(mock_scrape, client):
    res = client.post("/api/analyze", json={"url": "https://down.example.com"})
    assert res.status_code == 400
    assert "detail" in res.json()


def test_text_analysis_still_works(client):
    text = (
        "We may share your personal data with third-party advertising partners. "
        "You agree to binding arbitration for any disputes that arise from use of this service."
    )
    res = client.post("/api/analyze", json={"text": text})
    assert res.status_code == 200
    body = res.json()
    assert "id" in body
    assert body["status"] == "processing"

    analysis = _poll_until_complete(client, body["id"])
    assert analysis["status"] == "complete"
    assert analysis["clause_count"] > 0
