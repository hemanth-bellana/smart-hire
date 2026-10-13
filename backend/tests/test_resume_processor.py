
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.models.candidate import Candidate
from app.models.resume import Resume
from app.services.resume_processor import process_resume_file


@pytest.fixture
def db():
    session = MagicMock()
    added_objects = []

    def add_object(obj):
        added_objects.append(obj)

    def flush_objects():
        for obj in added_objects:
            if isinstance(obj, Candidate) and obj.id is None:
                obj.id = 101
            elif isinstance(obj, Resume) and obj.id is None:
                obj.id = 201

    session.add.side_effect = add_object
    session.flush.side_effect = flush_objects
    session.refresh.side_effect = lambda obj: None

    return session


@pytest.fixture
def job():
    return SimpleNamespace(id=10)


@pytest.fixture
def profile():
    return {
        "name": "Alex Example",
        "email": "alex@example.com",
        "phone": "9876543210",
        "location": "Hyderabad",
        "skills": ["Python", "SQL"],
        "education": "B.Tech",
        "experience_years": 2,
        "previous_companies": ["Example Corp"],
        "certifications": ["AWS"],
    }


def test_processes_pdf_resume_successfully(db, job, profile):
    with (
        patch(
            "app.services.resume_processor.extract_text_from_pdf",
            return_value="Alex Example - Python developer",
        ),
        patch(
            "app.services.resume_processor.extract_candidate_profile",
            return_value=profile,
        ),
    ):
        candidate, resume = process_resume_file(
            db=db,
            file_path="uploads/alex.pdf",
            original_filename="alex.pdf",
            stored_filename="stored-alex.pdf",
            file_type="application/pdf",
            file_size=1024,
            job=job,
        )

    assert candidate.id == 101
    assert candidate.job_id == job.id
    assert candidate.name == "Alex Example"
    assert candidate.skills == "Python, SQL"
    assert candidate.resume_text == "Alex Example - Python developer"
    assert resume.id == 201
    assert resume.candidate_id == candidate.id
    assert resume.processing_status == "COMPLETED"
    db.commit.assert_called_once()
    db.rollback.assert_not_called()


def test_marks_resume_failed_when_no_text_is_extracted(db, job):
    with patch(
        "app.services.resume_processor.extract_text_from_pdf",
        return_value="   \n ",
    ):
        candidate, resume = process_resume_file(
            db=db,
            file_path="uploads/empty.pdf",
            original_filename="empty.pdf",
            stored_filename="empty.pdf",
            file_type="application/pdf",
            file_size=100,
            job=job,
        )

    assert candidate.id == 101
    assert resume.candidate_id == candidate.id
    assert resume.processing_status == "FAILED"
    db.commit.assert_called_once()
    db.rollback.assert_not_called()


def test_rolls_back_when_pdf_parsing_fails(db, job):
    with patch(
        "app.services.resume_processor.extract_text_from_pdf",
        side_effect=ValueError("Invalid PDF"),
    ):
        with pytest.raises(ValueError, match="Invalid PDF"):
            process_resume_file(
                db=db,
                file_path="uploads/broken.pdf",
                original_filename="broken.pdf",
                stored_filename="broken.pdf",
                file_type="application/pdf",
                file_size=100,
                job=job,
            )

    db.rollback.assert_called_once()
    db.commit.assert_not_called()


def test_requires_exactly_one_parent_record(db):
    with pytest.raises(ValueError, match="exactly one"):
        process_resume_file(
            db=db,
            file_path="uploads/alex.pdf",
            original_filename="alex.pdf",
            stored_filename="alex.pdf",
            file_type="application/pdf",
            file_size=100,
        )

    with pytest.raises(ValueError, match="exactly one"):
        process_resume_file(
            db=db,
            file_path="uploads/alex.pdf",
            original_filename="alex.pdf",
            stored_filename="alex.pdf",
            file_type="application/pdf",
            file_size=100,
            job=SimpleNamespace(id=10),
            screening=SimpleNamespace(id=20),
        )

    db.add.assert_not_called()
