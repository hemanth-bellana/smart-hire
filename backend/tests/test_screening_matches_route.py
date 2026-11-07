
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.db.database import get_db
from app.api.routes import screening as screening_route


@pytest.fixture
def setup_screening_matches(monkeypatch):
    app = FastAPI()
    app.include_router(screening_route.router)

    user = SimpleNamespace(
        id=1,
        email="hr@example.com",
    )

    screening = SimpleNamespace(
        id=20,
        created_by=1,
        jd_filename="developer.pdf",
    )

    requirement = SimpleNamespace(
        screening_id=20,
    )

    candidates = [
        SimpleNamespace(
            id=101,
            name="Alex",
            email="alex@example.com",
            screening_id=20,
            skills="Python, SQL, Machine Learning",
            status="PROCESSED",
        ),
        SimpleNamespace(
            id=102,
            name="Sam",
            email="sam@example.com",
            screening_id=20,
            status="PROCESSING_FAILED",
        ),
        SimpleNamespace(
            id=103,
            name="John",
            email="john@example.com",
            screening_id=20,
            status="PENDING",
        ),
        SimpleNamespace(
            id=104,
            name="Priya",
            email="priya@example.com",
            screening_id=20,
            skills="Java, Spring Boot, SQL",
            status="PROCESSED",
        ),
    ]

    db = MagicMock()

    # Configure the three database queries:
    # 1. Screening lookup
    # 2. Screening requirement lookup
    # 3. Candidate lookup
    screening_query = MagicMock()
    requirement_query = MagicMock()
    candidate_query = MagicMock()

    db.query.side_effect = [
        screening_query,
        requirement_query,
        candidate_query,
    ]

    screening_query.filter.return_value.first.return_value = screening
    requirement_query.filter.return_value.first.return_value = requirement
    candidate_query.filter.return_value.order_by.return_value.all.return_value = (
        candidates
    )

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: user

    return {
        "client": TestClient(app),
        "candidates": candidates,
        "monkeypatch": monkeypatch,
    }


# Reusable fake matching function for filter tests.
def configure_fake_matching(monkeypatch):
    def fake_match_candidate_against_screening(
        candidate,
        requirement,
        screening,
    ):
        return {
            "candidate_id": candidate.id,
            "eligibility_status": (
                "ELIGIBLE"
                if candidate.id == 101
                else "NEEDS_REVIEW"
            ),
            "overall_score": (
                85 if candidate.id == 101 else 65
            ),
        }

    monkeypatch.setattr(
        screening_route,
        "match_candidate_against_screening",
        fake_match_candidate_against_screening,
    )

    monkeypatch.setattr(
        screening_route,
        "rank_matches",
        lambda matches: matches,
    )


# ---------------------------------------------------------
# Existing tests
# ---------------------------------------------------------

def test_matches_only_processed_candidates(setup_screening_matches):
    matched_candidate_ids = []

    def fake_match_candidate_against_screening(
        candidate,
        requirement,
        screening,
    ):
        matched_candidate_ids.append(candidate.id)

        return {
            "candidate_id": candidate.id,
            "eligibility_status": (
                "ELIGIBLE"
                if candidate.id == 101
                else "NEEDS_REVIEW"
            ),
            "overall_score": (
                85 if candidate.id == 101 else 65
            ),
        }

    setup_screening_matches["monkeypatch"].setattr(
        screening_route,
        "match_candidate_against_screening",
        fake_match_candidate_against_screening,
    )

    setup_screening_matches["monkeypatch"].setattr(
        screening_route,
        "rank_matches",
        lambda matches: matches,
    )

    response = setup_screening_matches["client"].get(
        "/screening/20/matches"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total_candidates"] == 4
    assert body["processed_candidates"] == 2
    assert body["processing_failed_candidates"] == 1
    assert body["pending_candidates"] == 1
    assert body["total_matches"] == 2

    assert matched_candidate_ids == [101, 104]

    assert [
        match["candidate_status"]
        for match in body["matches"]
    ] == [
        "PROCESSED",
        "PROCESSED",
    ]


def test_matches_return_empty_when_no_candidates_are_processed(
    setup_screening_matches,
):
    setup_screening_matches["candidates"][:] = [
        SimpleNamespace(
            id=102,
            name="Sam",
            email="sam@example.com",
            screening_id=20,
            status="PROCESSING_FAILED",
        ),
        SimpleNamespace(
            id=103,
            name="John",
            email="john@example.com",
            screening_id=20,
            status="PENDING",
        ),
    ]

    def unexpected_match(*args, **kwargs):
        pytest.fail(
            "Matching should not run for unprocessed candidates"
        )

    setup_screening_matches["monkeypatch"].setattr(
        screening_route,
        "match_candidate_against_screening",
        unexpected_match,
    )

    setup_screening_matches["monkeypatch"].setattr(
        screening_route,
        "rank_matches",
        lambda matches: matches,
    )

    response = setup_screening_matches["client"].get(
        "/screening/20/matches"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total_candidates"] == 2
    assert body["processed_candidates"] == 0
    assert body["processing_failed_candidates"] == 1
    assert body["pending_candidates"] == 1
    assert body["total_matches"] == 0
    assert body["matches"] == []


# ---------------------------------------------------------
# New filtering tests
# ---------------------------------------------------------

def test_filter_matches_by_eligibility_status(
    setup_screening_matches,
):
    data = setup_screening_matches
    configure_fake_matching(data["monkeypatch"])

    response = data["client"].get(
        "/screening/20/matches?eligibility_status=ELIGIBLE"
    )

    assert response.status_code == 200

    matches = response.json()["matches"]

    assert len(matches) == 1
    assert matches[0]["candidate_id"] == 101
    assert matches[0]["eligibility_status"] == "ELIGIBLE"


def test_filter_matches_by_minimum_score(
    setup_screening_matches,
):
    data = setup_screening_matches
    configure_fake_matching(data["monkeypatch"])

    response = data["client"].get(
        "/screening/20/matches?min_score=70"
    )

    assert response.status_code == 200

    matches = response.json()["matches"]

    assert len(matches) == 1
    assert matches[0]["candidate_id"] == 101
    assert matches[0]["overall_score"] == 85


def test_filter_matches_by_skill(
    setup_screening_matches,
):
    data = setup_screening_matches
    configure_fake_matching(data["monkeypatch"])

    response = data["client"].get(
        "/screening/20/matches?skill=Spring"
    )

    assert response.status_code == 200

    matches = response.json()["matches"]

    assert len(matches) == 1
    assert matches[0]["candidate_id"] == 104


def test_filter_matches_using_multiple_filters(
    setup_screening_matches,
):
    data = setup_screening_matches
    configure_fake_matching(data["monkeypatch"])

    response = data["client"].get(
        "/screening/20/matches"
        "?eligibility_status=NEEDS_REVIEW"
        "&min_score=60"
        "&skill=Java"
    )

    assert response.status_code == 200

    matches = response.json()["matches"]

    assert len(matches) == 1
    assert matches[0]["candidate_id"] == 104
    assert matches[0]["eligibility_status"] == "NEEDS_REVIEW"
    assert matches[0]["overall_score"] == 65


def test_reject_invalid_eligibility_status(
    setup_screening_matches,
):
    response = setup_screening_matches["client"].get(
        "/screening/20/matches?eligibility_status=INVALID"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid eligibility status"
