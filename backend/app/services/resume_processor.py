from pathlib import Path

from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.job import Job
from app.models.resume import Resume
from app.services.docx_parser import extract_text_from_docx
from app.services.pdf_parser import extract_text_from_pdf


def process_resume_file(
    db: Session,
    job: Job,
    file_path: str,
    original_filename: str,
    stored_filename: str,
    file_type: str,
    file_size: int,
) -> tuple[Candidate, Resume]:
    """
    Create candidate and resume records for a single PDF/DOCX resume
    and extract its text.
    """

    candidate = Candidate(
        job_id=job.id,
        status="PENDING",
    )

    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    resume = Resume(
        candidate_id=candidate.id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        file_path=file_path,
        file_type=file_type,
        file_size=file_size,
        processing_status="UPLOADED",
    )

    db.add(resume)
    db.commit()
    db.refresh(resume)

    extension = Path(original_filename).suffix.lower()

    if extension == ".pdf":
        extracted_text = extract_text_from_pdf(file_path)

    elif extension == ".docx":
        extracted_text = extract_text_from_docx(file_path)

    else:
        extracted_text = ""

    if extracted_text:
        candidate.resume_text = extracted_text
        resume.processing_status = "COMPLETED"

        db.commit()
        db.refresh(candidate)
        db.refresh(resume)

    return candidate, resume