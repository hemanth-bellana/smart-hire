
import logging
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


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/jobs",
    tags=["Resumes"],
)

UPLOAD_DIRECTORY = Path("uploads/resumes")


def _remove_file(file_path: Path) -> None:
    """Try to remove a temporary file without masking another error."""
    try:
        file_path.unlink(missing_ok=True)
    except OSError:
        logger.warning("Could not remove temporary file: %s", file_path)


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

    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume filename is missing.",
        )

    contents = await validate_resume_file(file)
    extension = Path(file.filename).suffix.lower()

    UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)

    stored_filename = f"{uuid4().hex}{extension}"
    file_path = UPLOAD_DIRECTORY / stored_filename
    file_path.write_bytes(contents)

    # ZIP upload: process each extracted resume independently.
    if extension == ".zip":
        zip_extract_directory = (
            UPLOAD_DIRECTORY / f"zip_{uuid4().hex}"
        )

        try:
            validate_zip_file(str(file_path))

            extracted_files = extract_zip_file(
                zip_path=str(file_path),
                extract_directory=str(zip_extract_directory),
            )

            processed_resumes = []

            for extracted_file in extracted_files:
                extracted_path = Path(extracted_file)

                if extracted_path.suffix.lower() == ".pdf":
                    file_type = "application/pdf"
                else:
                    file_type = (
                        "application/"
                        "vnd.openxmlformats-officedocument."
                        "wordprocessingml.document"
                    )

                try:
                    candidate, resume = process_resume_file(
                        db=db,
                        job=job,
                        file_path=str(extracted_path),
                        original_filename=extracted_path.name,
                        stored_filename=extracted_path.name,
                        file_type=file_type,
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

                except Exception:
                    logger.exception(
                        "Failed to process ZIP resume: %s",
                        extracted_path.name,
                    )

                    _remove_file(extracted_path)

                    processed_resumes.append(
                        {
                            "candidate_id": None,
                            "resume_id": None,
                            "filename": extracted_path.name,
                            "processing_status": "FAILED",
                            "error": "Resume processing failed.",
                        }
                    )

            statuses = [
                item["processing_status"]
                for item in processed_resumes
            ]

            completed_count = statuses.count("COMPLETED")
            failed_count = statuses.count("FAILED")

            if failed_count == 0:
                batch_status = "COMPLETED"
            elif completed_count == 0:
                batch_status = "FAILED"
            else:
                batch_status = "PARTIAL"

            return {
                "message": "ZIP resume processing finished.",
                "job_id": job.id,
                "original_filename": file.filename,
                "file_size": len(contents),
                "processing_status": batch_status,
                "total_resumes": len(processed_resumes),
                "completed_resumes": completed_count,
                "failed_resumes": failed_count,
                "resume_files": processed_resumes,
            }

        except HTTPException:
            raise
        except Exception as exc:
            logger.exception("Failed to process ZIP upload.")
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="The ZIP file could not be processed.",
            ) from exc
        finally:
            # The original ZIP is temporary and should always be removed.
            _remove_file(file_path)

            # Remove the extraction directory only if it is empty.
            try:
                zip_extract_directory.rmdir()
            except FileNotFoundError:
                pass
            except OSError:
                logger.debug(
                    "Retaining non-empty ZIP extraction directory: %s",
                    zip_extract_directory,
                )
    # Single PDF/DOCX ufinallypload.
    try:
        candidate, resume = process_resume_file(
            db=db,
            job=job,
            file_path=str(file_path),
            original_filename=file.filename,
            stored_filename=stored_filename,
            file_type=file.content_type or "application/octet-stream",
            file_size=len(contents),
        )

        return {
            "message": "Resume uploaded successfully.",
            "job_id": job.id,
            "candidate_id": candidate.id,
            "resume_id": resume.id,
            "original_filename": file.filename,
            "stored_filename": stored_filename,
            "file_size": len(contents),
            "processing_status": resume.processing_status,
        }

    except Exception as exc:
        logger.exception(
            "Failed to process uploaded resume: %s",
            file.filename,
        )
        _remove_file(file_path)

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="The uploaded resume could not be processed.",
        ) from exc
