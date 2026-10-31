
from types import SimpleNamespace
from unittest.mock import MagicMock
from pathlib import Path
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
        "upload_directory": upload_directory,
        "monkeypatch": monkeypatch,
    }


def configure_zip_processing(setup, filenames, outcomes):
    extracted_files = []

    def fake_extract(zip_path, extract_directory):
        directory = Path(extract_directory)
        directory.mkdir(parents=True, exist_ok=True)

        files = []

        for name in filenames:
            path = directory / name
            path.write_bytes(b"test resume content")
            files.append(str(path))

        extracted_files.extend(files)
        return files

    setup["monkeypatch"].setattr(
        resumes_route,
        "extract_zip_file",
        fake_extract,
    )

    processed_names = []
    outcome_iter = iter(outcomes)

    def fake_process_resume_file(**kwargs):
        name = kwargs["original_filename"]
        processed_names.append(name)

        outcome = next(outcome_iter)

        if isinstance(outcome, Exception):
            raise outcome

        candidate = SimpleNamespace(id=len(processed_names) + 100)
        resume = SimpleNamespace(
            id=len(processed_names) + 200,
            processing_status=outcome,
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
    remaining_directories = list(
        setup_route["upload_directory"].glob("zip_*")
    )

    assert len(remaining_directories) == 1

    retained_files = list(
        remaining_directories[0].glob("*")
    )

    assert len(retained_files) == 2
    assert all(path.exists() for path in retained_files)
    zip_files = list(
        setup_route["upload_directory"].glob("*.zip")
    )
    assert zip_files == []
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
    remaining_directories = list(
        setup_route["upload_directory"].glob("zip_*")
    )

    assert len(remaining_directories) == 1

    retained_files = list(
        remaining_directories[0].glob("*")
    )

    assert len(retained_files) == 1
    assert retained_files[0].name == "two.pdf"
    assert retained_files[0].exists()


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
    remaining_directories = list(
    setup_route["upload_directory"].glob("zip_*")
    )
    assert remaining_directories == []
    remaining_directories = list(
    setup_route["upload_directory"].glob("zip_*")
)
    assert remaining_directories == []
    zip_files = list(
    setup_route["upload_directory"].glob("*.zip")
    )
    assert zip_files == []
def test_invalid_zip_upload_removes_original_file(setup_route):
    setup_route["monkeypatch"].setattr(
        resumes_route,
        "validate_zip_file",
        lambda path: (_ for _ in ()).throw(
            ValueError("Invalid ZIP archive")
        ),
    )

    response = upload_zip(setup_route["client"])

    assert response.status_code == 422

    zip_files = list(
        setup_route["upload_directory"].glob("*.zip")
    )
    assert zip_files == []

    extraction_directories = list(
        setup_route["upload_directory"].glob("zip_*")
    )
    assert extraction_directories == []
def test_single_resume_upload_retains_file_on_success(setup_route):
    setup_route["monkeypatch"].setattr(
        resumes_route,
        "process_resume_file",
        lambda **kwargs: (
            SimpleNamespace(id=101),
            SimpleNamespace(id=201, processing_status="COMPLETED"),
        ),
    )

    response = setup_route["client"].post(
        "/jobs/10/resumes",
        files={
            "file": (
                "resume.pdf",
                b"%PDF-1.7 sample",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 200

    stored_files = list(
        setup_route["upload_directory"].glob("*.pdf")
    )

    assert len(stored_files) == 1
    assert stored_files[0].exists()
def test_single_resume_upload_removes_file_on_failure(setup_route):
    def fail_processing(**kwargs):
        raise ValueError("Simulated processing failure")

    setup_route["monkeypatch"].setattr(
        resumes_route,
        "process_resume_file",
        fail_processing,
    )

    response = setup_route["client"].post(
        "/jobs/10/resumes",
        files={
            "file": (
                "resume.pdf",
                b"%PDF-1.7 sample",
                "application/pdf",
            )
        },
    )

    assert response.status_code == 422

    stored_files = list(
        setup_route["upload_directory"].glob("*.pdf")
    )

    assert stored_files == []