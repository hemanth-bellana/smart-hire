
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.db.database import get_db
from app.api.routes import screening as screening_route


@pytest.fixture
def setup_screening_route(monkeypatch, tmp_path):
    # Keep relative file operations inside the temporary test directory.
    monkeypatch.chdir(tmp_path)

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
        jd_text="Python developer",
        status="CREATED",
    )

    # Mock database and screening lookup.
    db = MagicMock()
    screening_query = MagicMock()

    db.query.return_value = screening_query
    screening_query.filter.return_value.first.return_value = screening

    def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = lambda: user

    # Mock resume file validation.
    async def fake_validate_resume_file(file):
        return b"test zip content"

    monkeypatch.setattr(
        screening_route,
        "validate_resume_file",
        fake_validate_resume_file,
    )

    # Mock ZIP validation.
    monkeypatch.setattr(
        screening_route,
        "validate_zip_file",
        lambda path: ["one.pdf", "two.pdf"],
    )

    # Create simulated extracted resume files.
    extracted_dir = tmp_path / "extracted"
    extracted_dir.mkdir()

    def make_resume_file(name):
        path = extracted_dir / name
        path.write_bytes(b"test resume content")
        return str(path)

    monkeypatch.setattr(
        screening_route,
        "extract_zip_file",
        lambda zip_path, extract_directory: [
            make_resume_file("one.pdf"),
            make_resume_file("two.pdf"),
        ],
    )

    return {
        "client": TestClient(app),
        "db": db,
        "screening": screening,
        "monkeypatch": monkeypatch,
    }


def upload_zip(client):
    return client.post(
        "/screening/20/resumes",
        files={
            "file": (
                "resumes.zip",
                b"test zip content",
                "application/zip",
            )
        },
    )


def test_zip_upload_continues_after_one_resume_fails(
    setup_screening_route,
):
    processed_names = []

    def fake_process_resume_file(**kwargs):
        name = kwargs["original_filename"]
        processed_names.append(name)

        if name == "one.pdf":
            raise ValueError("simulated parser failure")

        candidate = SimpleNamespace(
            id=102,
            name="Alex Example",
            email="alex@example.com",
        )
        resume = SimpleNamespace(
            id=202,
            processing_status="COMPLETED",
        )

        return candidate, resume

    setup_screening_route["monkeypatch"].setattr(
        screening_route,
        "process_resume_file",
        fake_process_resume_file,
    )

    response = upload_zip(setup_screening_route["client"])

    assert response.status_code == 200

    body = response.json()

    assert body["total_resumes"] == 2
    assert [
        item["status"] for item in body["candidates"]
    ] == [
        "FAILED",
        "COMPLETED",
    ]
    assert processed_names == ["one.pdf", "two.pdf"]


def test_zip_upload_returns_failed_status_when_all_resumes_fail(
    setup_screening_route,
):
    def fake_process_resume_file(**kwargs):
        raise ValueError("simulated parser failure")

    setup_screening_route["monkeypatch"].setattr(
        screening_route,
        "process_resume_file",
        fake_process_resume_file,
    )

    response = upload_zip(setup_screening_route["client"])

    assert response.status_code == 200

    body = response.json()

    assert body["total_resumes"] == 2
    assert all(
        item["status"] == "FAILED"
        for item in body["candidates"]
    )
