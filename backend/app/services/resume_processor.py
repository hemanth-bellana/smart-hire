from pathlib import Path

from sqlalchemy.orm import Session

from app.models.candidate import Candidate
from app.models.job import Job
from app.models.resume import Resume
from app.models.Screening import Screening
from app.services.candidate_profile_extractor import extract_candidate_profile
from app.services.docx_parser import extract_text_from_docx
from app.services.pdf_parser import extract_text_from_pdf


def process_resume_file(
    db: Session,
    file_path: str,
    original_filename: str,
    stored_filename: str,
    file_type: str,
    file_size: int,
    job: Job | None = None,
    screening: Screening | None = None,
) -> tuple[Candidate, Resume]:

    if job is None and screening is None:
        raise ValueError(
            "Either job or screening must be provided."
        )

    if job is not None and screening is not None:
        raise ValueError(
            "Provide either job or screening, not both."
        )

    candidate = Candidate(
        job_id=job.id if job else None,
        screening_id=screening.id if screening else None,
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
        profile = extract_candidate_profile(extracted_text)

        candidate.resume_text = extracted_text
        candidate.name = profile["name"]
        candidate.email = profile["email"]
        candidate.phone = profile["phone"]
        candidate.location = profile["location"]

        candidate.skills = (
            ", ".join(profile["skills"])
            if profile["skills"]
            else None
        )

        candidate.education = profile["education"]

        candidate.experience_years = profile["experience_years"]

        candidate.previous_companies = (
            ", ".join(profile["previous_companies"])
            if profile["previous_companies"]
            else None
        )

        candidate.certifications = (
            ", ".join(profile["certifications"])
            if profile["certifications"]
            else None
        )

        resume.processing_status = "COMPLETED"

        db.commit()
        db.refresh(candidate)
        db.refresh(resume)

    return candidate, resume