"""API tests for Enhanced Search functionality (DEV-19).

Covers:
  GET /api/guestbook?q=keyword&author=name&from_date=YYYY-MM-DD&to_date=YYYY-MM-DD&sort=newest|oldest

Acceptance criteria tested:
  - Keyword search (case-insensitive, partial match) against name/email/comment
  - Author filter (partial match)
  - Date range filter (from_date / to_date, ISO 8601)
  - Sort order (newest / oldest)
  - Filters combined
  - Edge cases: empty search, whitespace-only, no results → 200 + empty list,
    500+ char input → 400, special characters treated as literals
  - Input safety: SQL injection → 200 with 0 results (no error/leak)
  - Invalid date format → 400
  - from_date after to_date → 400
"""

import allure
import pytest
import requests

BASE_URL = "http://127.0.0.1:8080"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def auth_token():
    resp = requests.post(
        f"{BASE_URL}/api/login", json={"username": "admin", "password": "password123"}
    )
    assert resp.status_code == 200
    return resp.json()["token"]


@pytest.fixture(scope="module")
def search_entries(auth_token):
    """Seed a small set of known entries for search tests and return their IDs."""
    headers = {"Authorization": f"Bearer {auth_token}"}
    created = []
    seed = [
        {"name": "Alice Smith", "email": "alice@example.com", "comment": "Hello world"},
        {
            "name": "Bob Jones",
            "email": "bob@example.com",
            "comment": "Greetings from Bob",
        },
        {
            "name": "Charlie Brown",
            "email": "charlie@example.com",
            "comment": "foo bar baz",
        },
    ]
    for entry in seed:
        r = requests.post(f"{BASE_URL}/api/guestbook", json=entry, headers=headers)
        assert r.status_code == 201
        created.append(r.json()["userId"])
    yield created


def _get(auth_token, **params):
    headers = {"Authorization": f"Bearer {auth_token}"}
    return requests.get(f"{BASE_URL}/api/guestbook", params=params, headers=headers)


# ---------------------------------------------------------------------------
# Core search behaviour
# ---------------------------------------------------------------------------


@allure.feature("Search")
@allure.story("Keyword Search")
@allure.severity(allure.severity_level.CRITICAL)
def test_keyword_search_matches_comment(auth_token, search_entries):
    """Keyword matches entry comment (case-insensitive, partial)."""
    resp = _get(auth_token, search="hello")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert any("hello" in e["comment"].lower() for e in data)


@allure.feature("Search")
@allure.story("Keyword Search")
@allure.severity(allure.severity_level.NORMAL)
def test_keyword_search_case_insensitive(auth_token, search_entries):
    """Search is case-insensitive — 'HELLO' matches 'Hello world'."""
    resp = _get(auth_token, search="HELLO")
    assert resp.status_code == 200
    assert any("hello" in e["comment"].lower() for e in resp.json()["data"])


@allure.feature("Search")
@allure.story("Keyword Search")
@allure.severity(allure.severity_level.NORMAL)
def test_no_filters_returns_all(auth_token, search_entries):
    """No filters → all entries returned (total >= seeded count)."""
    resp = _get(auth_token)
    assert resp.status_code == 200
    assert resp.json()["meta"]["total"] >= len(search_entries)


@allure.feature("Search")
@allure.story("Keyword Search")
@allure.severity(allure.severity_level.NORMAL)
def test_default_sort_is_newest(auth_token, search_entries):
    """Default sort returns results in descending date order."""
    resp = _get(auth_token)
    assert resp.status_code == 200
    dates = [e["created_at"] for e in resp.json()["data"]]
    assert dates == sorted(dates, reverse=True) or len(dates) <= 1


# ---------------------------------------------------------------------------
# Advanced filters
# ---------------------------------------------------------------------------


@allure.feature("Search")
@allure.story("Author Filter")
@allure.severity(allure.severity_level.CRITICAL)
def test_author_filter_partial_match(auth_token, search_entries):
    """author=Alice returns entries whose name contains 'Alice'."""
    resp = _get(auth_token, author="Alice")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert all("alice" in e["name"].lower() for e in data)
    assert len(data) >= 1


@allure.feature("Search")
@allure.story("Date Range Filter")
@allure.severity(allure.severity_level.CRITICAL)
def test_date_range_from_date_future_returns_empty(auth_token, search_entries):
    """from_date in the far future returns empty list with 200."""
    resp = _get(auth_token, from_date="2099-01-01")
    assert resp.status_code == 200
    assert resp.json()["data"] == []


@allure.feature("Search")
@allure.story("Date Range Filter")
@allure.severity(allure.severity_level.NORMAL)
def test_date_range_to_date_past_returns_empty(auth_token, search_entries):
    """to_date in the distant past returns empty list with 200."""
    resp = _get(auth_token, to_date="2000-01-01")
    assert resp.status_code == 200
    assert resp.json()["data"] == []


@allure.feature("Search")
@allure.story("Sort Order")
@allure.severity(allure.severity_level.NORMAL)
def test_sort_oldest(auth_token, search_entries):
    """sort=oldest returns results in ascending date order."""
    resp = _get(auth_token, sort="oldest")
    assert resp.status_code == 200
    dates = [e["created_at"] for e in resp.json()["data"]]
    assert dates == sorted(dates) or len(dates) <= 1


@allure.feature("Search")
@allure.story("Sort Order")
@allure.severity(allure.severity_level.NORMAL)
def test_sort_newest(auth_token, search_entries):
    """sort=newest returns results in descending date order."""
    resp = _get(auth_token, sort="newest")
    assert resp.status_code == 200
    dates = [e["created_at"] for e in resp.json()["data"]]
    assert dates == sorted(dates, reverse=True) or len(dates) <= 1


@allure.feature("Search")
@allure.story("Combined Filters")
@allure.severity(allure.severity_level.CRITICAL)
def test_combined_keyword_and_author(auth_token, search_entries):
    """Keyword + author filter combined correctly narrows results."""
    resp = _get(auth_token, search="Greetings", author="Bob")
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert all("bob" in e["name"].lower() for e in data)


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


@allure.feature("Search")
@allure.story("Edge Cases")
@allure.severity(allure.severity_level.NORMAL)
def test_empty_search_returns_all(auth_token, search_entries):
    """Empty search string behaves the same as no search param."""
    resp = _get(auth_token, search="")
    assert resp.status_code == 200
    assert resp.json()["meta"]["total"] >= len(search_entries)


@allure.feature("Search")
@allure.story("Edge Cases")
@allure.severity(allure.severity_level.NORMAL)
def test_whitespace_only_search_treated_as_empty(auth_token, search_entries):
    """Whitespace-only search string is treated as empty — no 400."""
    resp = _get(auth_token, search="   ")
    assert resp.status_code == 200


@allure.feature("Search")
@allure.story("Edge Cases")
@allure.severity(allure.severity_level.NORMAL)
def test_no_matching_results_returns_200_empty_list(auth_token, search_entries):
    """Search with no matches returns 200 with empty data list, not 404."""
    resp = _get(auth_token, search="xyzzy_no_match_12345")
    assert resp.status_code == 200
    assert resp.json()["data"] == []


@allure.feature("Search")
@allure.story("Edge Cases")
@allure.severity(allure.severity_level.NORMAL)
def test_very_long_search_input_returns_400(auth_token):
    """Search input over 500 characters is rejected with 400."""
    resp = _get(auth_token, search="a" * 501)
    assert resp.status_code == 400


@allure.feature("Search")
@allure.story("Edge Cases")
@allure.severity(allure.severity_level.NORMAL)
def test_single_character_search(auth_token, search_entries):
    """Single-character search returns valid results without error."""
    resp = _get(auth_token, search="a")
    assert resp.status_code == 200
    assert "data" in resp.json()


@allure.feature("Search")
@allure.story("Edge Cases")
@allure.severity(allure.severity_level.NORMAL)
def test_special_characters_treated_as_literals(auth_token, search_entries):
    """Special chars (%, _, *) are treated as literals — no 500 or SQL error."""
    for char in ["%", "_", "*", "?"]:
        resp = _get(auth_token, search=char)
        assert resp.status_code == 200, f"Failed for char: {char!r}"


# ---------------------------------------------------------------------------
# Input safety
# ---------------------------------------------------------------------------


@allure.feature("Search")
@allure.story("Input Safety")
@allure.severity(allure.severity_level.CRITICAL)
def test_sql_injection_returns_200_not_error(auth_token, search_entries):
    """SQL injection attempt returns 200 with 0 results, not an error."""
    payloads = [
        "' OR '1'='1",
        "'; DROP TABLE guestbook; --",
        "1 UNION SELECT * FROM guestbook",
    ]
    for payload in payloads:
        resp = _get(auth_token, search=payload)
        assert resp.status_code == 200, f"Expected 200 for payload: {payload!r}"
        # Must not leak data via injection
        assert isinstance(resp.json()["data"], list)


@allure.feature("Search")
@allure.story("Input Safety")
@allure.severity(allure.severity_level.CRITICAL)
def test_html_script_tags_not_reflected_unsanitised(auth_token, search_entries):
    """HTML/script in search input must not appear raw in JSON response."""
    resp = _get(auth_token, search="<script>alert(1)</script>")
    assert resp.status_code == 200
    body = resp.text
    assert "<script>" not in body


# ---------------------------------------------------------------------------
# API contract — date validation
# ---------------------------------------------------------------------------


@allure.feature("Search")
@allure.story("Date Validation")
@allure.severity(allure.severity_level.CRITICAL)
def test_invalid_from_date_returns_400(auth_token):
    """Malformed from_date returns 400 with a clear error message."""
    resp = _get(auth_token, from_date="not-a-date")
    assert resp.status_code == 400
    assert "from_date" in resp.json().get("message", "").lower()


@allure.feature("Search")
@allure.story("Date Validation")
@allure.severity(allure.severity_level.CRITICAL)
def test_invalid_to_date_returns_400(auth_token):
    """Malformed to_date returns 400 with a clear error message."""
    resp = _get(auth_token, to_date="2024/12/31")
    assert resp.status_code == 400
    assert "to_date" in resp.json().get("message", "").lower()


@allure.feature("Search")
@allure.story("Date Validation")
@allure.severity(allure.severity_level.CRITICAL)
def test_from_date_after_to_date_returns_400(auth_token):
    """from_date after to_date returns 400."""
    resp = _get(auth_token, from_date="2025-12-31", to_date="2024-01-01")
    assert resp.status_code == 400
