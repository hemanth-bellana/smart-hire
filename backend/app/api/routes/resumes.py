from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.resume import Resume
from app.models.user import User
from app.services.docx_parser import extract_text_from_docx
from app.services.pdf_parser import extract_text_from_pdf
from app.utils.file_utils import validate_resume_file


router = APIRouter(
    prefix="/jobs",
    tags=["Resumes"],
)


UPLOAD_DIRECTORY = Path("uploads/resumes")


@router.post("/{job_id}/resumes")
async def upload_resume(
    job_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    user = (
        db.query(User)
        .filter(User.email == current_user)
        .first()
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    job = (
        db.query(Job)
        .filter(
            Job.id == job_id,
            Job.created_by == user.id,
        )
        .first()
    )

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    contents = await validate_resume_file(file)

    extension = Path(file.filename).suffix.lower()
    stored_filename = f"{uuid4().hex}{extension}"

    UPLOAD_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path = UPLOAD_DIRECTORY / stored_filename

    file_path.write_bytes(contents)

    candidate = Candidate(
        job_id=job.id,
        status="PENDING",
    )

    db.add(candidate)
    db.commit()
    db.refresh(candidate)

    resume = Resume(
        candidate_id=candidate.id,
        original_filename=file.filename,
        stored_filename=stored_filename,
        file_path=str(file_path),
        file_type=file.content_type,
        file_size=len(contents),
        processing_status="UPLOADED",
    )

    db.add(resume)
    db.commit()
    db.refresh(resume)

    # Extract text based on the uploaded file type.
    if extension == ".pdf":
        extracted_text = extract_text_from_pdf(
            str(file_path)
        )

    elif extension == ".docx":
        extracted_text = extract_text_from_docx(
            str(file_path)
        )

    else:
        extracted_text = ""

    # Save extracted text to the candidate record.
    if extracted_text:
        candidate.resume_text = extracted_text
        resume.processing_status = "COMPLETED"

        db.commit()
        db.refresh(candidate)
        db.refresh(resume)

    return {
        "message": "Resume uploaded successfully",
        "job_id": job.id,
        "candidate_id": candidate.id,
        "resume_id": resume.id,
        "original_filename": file.filename,
        "stored_filename": stored_filename,
        "file_size": len(contents),
        "processing_status": resume.processing_status,
    }