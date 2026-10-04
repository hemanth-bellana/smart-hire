from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.job import Job
from app.models.user import User
from app.services.resume_processor import process_resume_file
from app.utils.file_utils import validate_resume_file
from app.utils.zip_utils import extract_zip_file, validate_zip_file


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

    # ---------------------------------------------------------
    # ZIP upload
    # ---------------------------------------------------------

    if extension == ".zip":
        valid_files = validate_zip_file(
            str(file_path)
        )

        zip_extract_directory = (
            UPLOAD_DIRECTORY / f"zip_{uuid4().hex}"
        )

        extracted_files = extract_zip_file(
            zip_path=str(file_path),
            extract_directory=str(zip_extract_directory),
        )

        processed_resumes = []

        for extracted_file in extracted_files:
            extracted_path = Path(extracted_file)

            candidate, resume = process_resume_file(
                db=db,
                job=job,
                file_path=str(extracted_path),
                original_filename=extracted_path.name,
                stored_filename=extracted_path.name,
                file_type=(
                    "application/pdf"
                    if extracted_path.suffix.lower() == ".pdf"
                    else (
                        "application/"
                        "vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
                ),
                file_size=extracted_path.stat().st_size,
            )

            processed_resumes.append(
                {
                    "candidate_id": candidate.id,
                    "resume_id": resume.id,
                    "filename": extracted_path.name,
                    "processing_status": resume.processing_status,
                }
            )

        return {
            "message": "ZIP resumes processed successfully",
            "job_id": job.id,
            "original_filename": file.filename,
            "stored_filename": stored_filename,
            "file_size": len(contents),
            "processing_status": "COMPLETED",
            "resume_files": processed_resumes,
        }

    # ---------------------------------------------------------
    # Single PDF/DOCX upload
    # ---------------------------------------------------------

    candidate, resume = process_resume_file(
        db=db,
        job=job,
        file_path=str(file_path),
        original_filename=file.filename,
        stored_filename=stored_filename,
        file_type=file.content_type,
        file_size=len(contents),
    )

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