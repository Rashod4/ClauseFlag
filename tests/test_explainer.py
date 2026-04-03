"""Unit tests for the Explainer 3-part structured explanation format."""

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from explainer import Explainer, get_explainer  # noqa: E402

EXPLANATION_KEYS = {"summary", "unusual", "risks"}


@pytest.fixture()
def explainer():
    return Explainer()


# ── Structure validation ────────────────────────────────────────────


def _assert_valid_explanation(result: dict):
    """Assert that a result dict has the right shape and non-empty strings."""
    assert "category" in result
    assert isinstance(result["category"], str)
    assert len(result["category"]) > 0

    exp = result["explanation"]
    assert isinstance(exp, dict), "explanation must be a dict"
    assert set(exp.keys()) == EXPLANATION_KEYS
    for key in EXPLANATION_KEYS:
        assert isinstance(exp[key], str), f"explanation.{key} must be a string"
        assert len(exp[key]) > 0, f"explanation.{key} must not be empty"


# ── Keyword rule tests ──────────────────────────────────────────────


@pytest.mark.parametrize(
    "keyword,text,expected_category",
    [
        ("sell", "We may sell your personal data.", "Data Selling"),
        ("arbitration", "You agree to binding arbitration.", "Dispute Resolution"),
        ("class action", "You waive class action rights.", "Dispute Resolution"),
        ("perpetual", "You grant us a perpetual license.", "IP Rights"),
        ("without notice", "We may terminate without notice.", "Termination"),
        ("indemnify", "You agree to indemnify the company.", "Liability"),
        ("location", "We collect your location data.", "Data Collection"),
        ("cookies", "We use cookies to track you.", "Tracking"),
        ("third party", "Data shared with third party vendors.", "Data Sharing"),
        ("anonymized", "Data is anonymized before sharing.", "Data Processing"),
        ("delete", "You may delete your account.", "Data Rights"),
        ("protect", "We protect your information.", "Security"),
    ],
)
def test_keyword_rules_return_structured_explanation(
    explainer, keyword, text, expected_category
):
    result = explainer.generate_explanation(text, "watch")
    _assert_valid_explanation(result)
    assert result["category"] == expected_category


def test_keyword_matching_is_case_insensitive(explainer):
    result = explainer.generate_explanation("BINDING ARBITRATION applies.", "safe")
    assert result["category"] == "Dispute Resolution"
    _assert_valid_explanation(result)


def test_first_keyword_match_wins(explainer):
    text = "We sell cookies and tracking data."
    result = explainer.generate_explanation(text, "watch")
    assert result["category"] == "Data Selling"
    _assert_valid_explanation(result)


# ── Fallback tests ──────────────────────────────────────────────────


@pytest.mark.parametrize("risk", ["safe", "watch", "danger"])
def test_fallback_returns_structured_explanation(explainer, risk):
    result = explainer.generate_explanation(
        "The service is provided as-is.", risk
    )
    _assert_valid_explanation(result)
    assert result["category"] == "General"


def test_fallback_unknown_risk_defaults_to_watch(explainer):
    result = explainer.generate_explanation(
        "Some generic clause text here.", "unknown_risk_level"
    )
    _assert_valid_explanation(result)
    assert result["category"] == "General"


# ── Singleton ───────────────────────────────────────────────────────


def test_get_explainer_returns_singleton():
    a = get_explainer()
    b = get_explainer()
    assert a is b


# ── Content quality checks ──────────────────────────────────────────


def test_danger_fallback_sounds_more_severe_than_safe(explainer):
    safe_res = explainer.generate_explanation("Basic terms apply.", "safe")
    danger_res = explainer.generate_explanation("Basic terms apply.", "danger")
    assert "minimal" in safe_res["explanation"]["risks"].lower()
    assert "limit" in danger_res["explanation"]["summary"].lower() or \
           "control" in danger_res["explanation"]["summary"].lower()


def test_all_rules_have_distinct_nonempty_parts(explainer):
    for keyword, data in explainer.rules.items():
        exp = data["explanation"]
        assert exp["summary"] != exp["unusual"], (
            f"Rule '{keyword}': summary and unusual should differ"
        )
        assert exp["summary"] != exp["risks"], (
            f"Rule '{keyword}': summary and risks should differ"
        )
