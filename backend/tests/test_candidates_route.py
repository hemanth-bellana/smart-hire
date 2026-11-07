
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_db
from app.api.routes import candidates as candidates_route


@pytest.fixture
def setup_candidates_route():
    app = FastAPI()
    app.include_router(candidates_route.router)

    user = SimpleNamespace(
        id=1,
        email="hr@example.com",
    )

    screening = SimpleNamespace(
        id=20,
        created_by=1,
    )

    candidate = SimpleNamespace(
        id=101,
        screening_id=20,
        name="Alex Example",
        email="alex@example.com",
        phone="9876543210",
        location="Hyderabad",
        skills="Python, SQL, Machine Learning",
        education="B.Tech Computer Science",
        experience_years=2,
        previous_companies="ABC Technologies",
        certifications="AWS Cloud Practitioner",
        match_score=85.5,
        status="PROCESSED",
        created_at=datetime(2026, 11, 6, 10, 30),
        resume_text="This is private raw resume text.",
    )

    db = MagicMock()

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = (
        lambda: "hr@example.com"
    )

    return {
        "client": TestClient(app),
        "db": db,
        "user": user,
        "screening": screening,
        "candidate": candidate,
    }


def configure_user_query(db, user):
    user_query = MagicMock()
    db.query.return_value = user_query
    user_query.filter.return_value.first.return_value = user
    return user_query


def test_list_screening_candidates_success(
    setup_candidates_route,
):
    data = setup_candidates_route
    db = data["db"]

    configure_user_query(db, data["user"])

    screening_query = MagicMock()
    candidate_query = MagicMock()

    db.query.side_effect = [
        db.query.return_value,
        screening_query,
        candidate_query,
    ]

    screening_query.filter.return_value.first.return_value = (
        data["screening"]
    )

    candidate_query.filter.return_value.order_by.return_value.all.return_value = [
        data["candidate"]
    ]

    response = data["client"].get(
        "/candidates/screening/20"
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1
    assert body[0]["id"] == 101
    assert body[0]["name"] == "Alex Example"
    assert body[0]["status"] == "PROCESSED"
    assert body[0]["match_score"] == 85.5
    assert "resume_text" not in body[0]


def test_list_screening_candidates_rejects_other_users_screening(
    setup_candidates_route,
):
    data = setup_candidates_route
    db = data["db"]

    configure_user_query(db, data["user"])

    screening_query = MagicMock()
    db.query.side_effect = [
        db.query.return_value,
        screening_query,
    ]

    screening_query.filter.return_value.first.return_value = None

    response = data["client"].get(
        "/candidates/screening/20"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Screening not found"


def test_list_screening_candidates_returns_404_for_missing_user(
    setup_candidates_route,
):
    data = setup_candidates_route
    db = data["db"]

    configure_user_query(db, None)

    response = data["client"].get(
        "/candidates/screening/20"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_get_candidate_success(setup_candidates_route):
    data = setup_candidates_route
    db = data["db"]

    configure_user_query(db, data["user"])

    candidate_query = MagicMock()
    db.query.side_effect = [
        db.query.return_value,
        candidate_query,
    ]

    candidate_query.join.return_value.filter.return_value.first.return_value = (
        data["candidate"]
    )

    response = data["client"].get("/candidates/101")

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == 101
    assert body["name"] == "Alex Example"
    assert body["email"] == "alex@example.com"
    assert body["status"] == "PROCESSED"
    assert "resume_text" not in body


def test_get_candidate_returns_404_when_not_found(
    setup_candidates_route,
):
    data = setup_candidates_route
    db = data["db"]

    configure_user_query(db, data["user"])

    candidate_query = MagicMock()
    db.query.side_effect = [
        db.query.return_value,
        candidate_query,
    ]

    candidate_query.join.return_value.filter.return_value.first.return_value = (
        None
    )

    response = data["client"].get("/candidates/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Candidate not found"

def test_list_candidates_filters_by_processing_status(
    setup_candidates_route,
):
    data = setup_candidates_route
    db = data["db"]

    configure_user_query(db, data["user"])

    screening_query = MagicMock()
    candidate_query = MagicMock()
    filtered_query = MagicMock()

    db.query.side_effect = [
        db.query.return_value,
        screening_query,
        candidate_query,
    ]

    screening_query.filter.return_value.first.return_value = (
        data["screening"]
    )

    candidate_query.filter.return_value = filtered_query

    filtered_query.filter.return_value.order_by.return_value.all.return_value = [
        data["candidate"]
    ]

    response = data["client"].get(
        "/candidates/screening/20?processing_status=PROCESSED"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == "PROCESSED"
    assert filtered_query.filter.called


def test_list_candidates_filters_by_skill(
    setup_candidates_route,
):
    data = setup_candidates_route
    db = data["db"]

    configure_user_query(db, data["user"])

    screening_query = MagicMock()
    candidate_query = MagicMock()
    filtered_query = MagicMock()

    db.query.side_effect = [
        db.query.return_value,
        screening_query,
        candidate_query,
    ]

    screening_query.filter.return_value.first.return_value = (
        data["screening"]
    )

    candidate_query.filter.return_value = filtered_query

    filtered_query.filter.return_value.order_by.return_value.all.return_value = [
        data["candidate"]
    ]

    response = data["client"].get(
        "/candidates/screening/20?skill=Python"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert "Python" in response.json()[0]["skills"]
    assert filtered_query.filter.called



def test_list_candidates_filters_by_status_and_skill(
    setup_candidates_route,
):
    data = setup_candidates_route
    db = data["db"]

    configure_user_query(db, data["user"])

    screening_query = MagicMock()
    candidate_query = MagicMock()
    status_query = MagicMock()
    skill_query = MagicMock()
    final_query = MagicMock()

    db.query.side_effect = [
        db.query.return_value,
        screening_query,
        candidate_query,
    ]

    screening_query.filter.return_value.first.return_value = (
        data["screening"]
    )

    candidate_query.filter.return_value = status_query
    status_query.filter.return_value = skill_query
    skill_query.filter.return_value = final_query

    final_query.order_by.return_value.all.return_value = [
        data["candidate"]
    ]

    response = data["client"].get(
        "/candidates/screening/20"
        "?processing_status=PROCESSED&skill=Python"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["status"] == "PROCESSED"
    assert "Python" in response.json()[0]["skills"]

def test_list_candidates_rejects_invalid_processing_status(
    setup_candidates_route,
):
    data = setup_candidates_route
    db = data["db"]

    configure_user_query(db, data["user"])

    screening_query = MagicMock()
    candidate_query = MagicMock()

    db.query.side_effect = [
        db.query.return_value,
        screening_query,
        candidate_query,
    ]

    screening_query.filter.return_value.first.return_value = (
        data["screening"]
    )

    response = data["client"].get(
        "/candidates/screening/20?processing_status=INVALID"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid processing status"
