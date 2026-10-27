
import logging
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.database import get_db
from app.models.candidate import Candidate
from app.models.Screening import Screening
from app.models.screening_requirement import ScreeningRequirement
from app.models.user import User
from app.services.docx_parser import extract_text_from_docx
from app.services.matching_service import match_candidate_against_screening
from app.services.pdf_parser import extract_text_from_pdf
from app.services.ranking_service import rank_matches
from app.services.resume_processor import process_resume_file
from app.services.screening_requirement_service import (
    analyze_and_save_screening_requirements,
)
from app.utils.file_utils import validate_resume_file
from app.utils.zip_utils import extract_zip_file, validate_zip_file

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/screening",
    tags=["Screening"],
)

UPLOAD_DIR = Path("uploads/screenings")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/jd")
async def upload_screening_jd(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    allowed_extensions = {".pdf", ".docx"}

    filename = file.filename or ""
    extension = Path(filename).suffix.lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX JD files are supported.",
        )

    file_content = await file.read()

    if not file_content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded JD file is empty.",
        )

    stored_filename = f"{uuid4().hex}{extension}"
    file_path = UPLOAD_DIR / stored_filename

    try:
        file_path.write_bytes(file_content)

        if extension == ".pdf":
            jd_text = extract_text_from_pdf(str(file_path))
        else:
            jd_text = extract_text_from_docx(str(file_path))

    except Exception as exc:
        logger.exception("Failed to extract text from job description")

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to extract text from the uploaded job description.",
        ) from exc

    if not jd_text or not jd_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No readable text was found in the JD.",
        )

    screening = Screening(
        created_by=current_user.id,
        jd_filename=filename,
        jd_text=jd_text,
        status="CREATED",
    )

    db.add(screening)
    db.commit()
    db.refresh(screening)

    analyze_and_save_screening_requirements(
        db=db,
        screening=screening,
    )

    return {
        "screening_id": screening.id,
        "jd_filename": screening.jd_filename,
        "status": screening.status,
    }


@router.post("/{screening_id}/resumes")
async def upload_screening_resume(
    screening_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    screening = (
        db.query(Screening)
        .filter(
            Screening.id == screening_id,
            Screening.created_by == current_user.id,
        )
        .first()
    )

    if not screening:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Screening not found.",
        )

    file_content = await validate_resume_file(file)
    extension = Path(file.filename or "").suffix.lower()

    screening_dir = Path("uploads/screenings") / str(screening_id)
    screening_dir.mkdir(parents=True, exist_ok=True)

    # Process a ZIP containing multiple resumes independently.
    if extension == ".zip":
        stored_filename = f"{uuid4().hex}.zip"
        zip_path = screening_dir / stored_filename
        zip_path.write_bytes(file_content)

        try:
            validate_zip_file(str(zip_path))

            extract_dir = screening_dir / uuid4().hex

            extracted_files = extract_zip_file(
                str(zip_path),
                str(extract_dir),
            )

        except HTTPException:
            raise
        except Exception as exc:
            logger.exception(
                "Failed to validate or extract ZIP for screening %s",
                screening_id,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unable to validate or extract the uploaded ZIP file.",
            ) from exc

        candidates = []

        for extracted_file in extracted_files:
            resume_path = Path(extracted_file)
            original_filename = resume_path.name

            try:
                file_size = resume_path.stat().st_size

                candidate, resume = process_resume_file(
                    db=db,
                    file_path=str(resume_path),
                    original_filename=original_filename,
                    stored_filename=original_filename,
                    file_type=resume_path.suffix.lstrip(".").lower(),
                    file_size=file_size,
                    screening=screening,
                )

                candidates.append(
                    {
                        "candidate_id": candidate.id,
                        "resume_id": resume.id,
                        "name": candidate.name,
                        "email": candidate.email,
                        "status": resume.processing_status,
                    }
                )

            except Exception:
                # A failure for one resume must not stop the remaining files.
                logger.exception(
                    "Failed to process resume %s for screening %s",
                    original_filename,
                    screening_id,
                )

                # If processing failed after partially changing the session,
                # roll back before processing the next resume.
                try:
                    db.rollback()
                except Exception:
                    logger.exception(
                        "Database rollback failed for resume %s",
                        original_filename,
                    )

                candidates.append(
                    {
                        "candidate_id": None,
                        "resume_id": None,
                        "name": None,
                        "email": None,
                        "status": "FAILED",
                    }
                )

        return {
            "screening_id": screening.id,
            "file_type": "zip",
            "total_resumes": len(candidates),
            "candidates": candidates,
        }

    # Process a single PDF or DOCX resume.
    stored_filename = f"{uuid4().hex}{extension}"
    file_path = screening_dir / stored_filename
    file_path.write_bytes(file_content)

    candidate, resume = process_resume_file(
        db=db,
        file_path=str(file_path),
        original_filename=file.filename or stored_filename,
        stored_filename=stored_filename,
        file_type=extension.lstrip("."),
        file_size=len(file_content),
        screening=screening,
    )

    return {
        "screening_id": screening.id,
        "file_type": extension.lstrip("."),
        "total_resumes": 1,
        "candidates": [
            {
                "candidate_id": candidate.id,
                "resume_id": resume.id,
                "name": candidate.name,
                "email": candidate.email,
                "status": resume.processing_status,
            }
        ],
    }


@router.get("/{screening_id}/matches")
def get_screening_matches(
    screening_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Verify that this screening belongs to the logged-in HR user.
    screening = (
        db.query(Screening)
        .filter(
            Screening.id == screening_id,
            Screening.created_by == current_user.id,
        )
        .first()
    )

    if not screening:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Screening not found.",
        )

    # Retrieve the structured requirements for this screening.
    requirement = (
        db.query(ScreeningRequirement)
        .filter(
            ScreeningRequirement.screening_id == screening_id
        )
        .first()
    )

    if not requirement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Screening requirements not found.",
        )

    # Retrieve candidates associated with this screening.
    candidates = (
        db.query(Candidate)
        .filter(Candidate.screening_id == screening_id)
        .order_by(Candidate.id.asc())
        .all()
    )

    matches = []

    for candidate in candidates:
        result = match_candidate_against_screening(
            candidate=candidate,
            requirement=requirement,
            screening=screening,
        )

        result["candidate_name"] = candidate.name
        result["candidate_email"] = candidate.email

        matches.append(result)

    matches = rank_matches(matches)

    return {
        "screening_id": screening.id,
        "jd_filename": screening.jd_filename,
        "total_candidates": len(matches),
        "matches": matches,
    }
