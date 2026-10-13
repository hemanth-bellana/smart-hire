
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_user, get_db
from app.api.routes import resumes as resumes_route


@pytest.fixture
def setup_route(monkeypatch, tmp_path):
    app = FastAPI()
    app.include_router(resumes_route.router)

    user = SimpleNamespace(id=1, email="hr@example.com")
    job = SimpleNamespace(id=10, created_by=1)

    db = MagicMock()
    user_query = MagicMock()
    job_query = MagicMock()

    db.query.side_effect = [user_query, job_query]
    user_query.filter.return_value.first.return_value = user
    job_query.filter.return_value.first.return_value = job

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = (
        lambda: "hr@example.com"
    )

    upload_directory = tmp_path / "uploads"
    monkeypatch.setattr(
        resumes_route,
        "UPLOAD_DIRECTORY",
        upload_directory,
    )

    extracted_directory = tmp_path / "extracted"
    extracted_directory.mkdir()

    def make_resume_file(name):
        path = extracted_directory / name
        path.write_bytes(b"test resume content")
        return str(path)

    async def fake_validate_resume_file(file):
        return b"test zip content"

    monkeypatch.setattr(
        resumes_route,
        "validate_resume_file",
        fake_validate_resume_file,
    )
    monkeypatch.setattr(
        resumes_route,
        "validate_zip_file",
        lambda path: ["one.pdf", "two.pdf"],
    )

    client = TestClient(app)

    return {
        "client": client,
        "db": db,
        "job": job,
        "make_resume_file": make_resume_file,
        "monkeypatch": monkeypatch,
    }


def configure_zip_processing(setup, filenames, outcomes):
    extracted_files = [
        setup["make_resume_file"](name)
        for name in filenames
    ]

    setup["monkeypatch"].setattr(
        resumes_route,
        "extract_zip_file",
        lambda zip_path, extract_directory: extracted_files,
    )

    processed_names = []
    outcome_iter = iter(outcomes)

    def fake_process_resume_file(**kwargs):
        name = kwargs["original_filename"]
        processed_names.append(name)

        outcome = next(outcome_iter)

        if isinstance(outcome, Exception):
            raise outcome

        status_value = outcome
        candidate = SimpleNamespace(id=len(processed_names) + 100)
        resume = SimpleNamespace(
            id=len(processed_names) + 200,
            processing_status=status_value,
        )
        return candidate, resume

    setup["monkeypatch"].setattr(
        resumes_route,
        "process_resume_file",
        fake_process_resume_file,
    )

    return processed_names


def upload_zip(client):
    return client.post(
        "/jobs/10/resumes",
        files={
            "file": (
                "resumes.zip",
                b"test zip content",
                "application/zip",
            )
        },
    )


def test_zip_batch_returns_completed_when_all_succeed(setup_route):
    processed_names = configure_zip_processing(
        setup_route,
        ["one.pdf", "two.pdf"],
        ["COMPLETED", "COMPLETED"],
    )

    response = upload_zip(setup_route["client"])

    assert response.status_code == 200

    body = response.json()
    assert body["processing_status"] == "COMPLETED"
    assert body["total_resumes"] == 2
    assert body["completed_resumes"] == 2
    assert body["failed_resumes"] == 0
    assert len(body["resume_files"]) == 2
    assert processed_names == ["one.pdf", "two.pdf"]


def test_zip_batch_returns_partial_and_continues_after_error(
    setup_route,
):
    processed_names = configure_zip_processing(
        setup_route,
        ["one.pdf", "two.pdf"],
        [ValueError("simulated parser failure"), "COMPLETED"],
    )

    response = upload_zip(setup_route["client"])

    assert response.status_code == 200

    body = response.json()
    assert body["processing_status"] == "PARTIAL"
    assert body["total_resumes"] == 2
    assert body["completed_resumes"] == 1
    assert body["failed_resumes"] == 1
    assert body["resume_files"][0]["processing_status"] == "FAILED"
    assert body["resume_files"][0]["candidate_id"] is None
    assert body["resume_files"][1]["processing_status"] == "COMPLETED"
    assert processed_names == ["one.pdf", "two.pdf"]


def test_zip_batch_returns_failed_when_all_processing_raises(
    setup_route,
):
    processed_names = configure_zip_processing(
        setup_route,
        ["one.pdf", "two.pdf"],
        [
            ValueError("first parser failure"),
            ValueError("second parser failure"),
        ],
    )

    response = upload_zip(setup_route["client"])

    assert response.status_code == 200

    body = response.json()
    assert body["processing_status"] == "FAILED"
    assert body["total_resumes"] == 2
    assert body["completed_resumes"] == 0
    assert body["failed_resumes"] == 2
    assert processed_names == ["one.pdf", "two.pdf"]
