
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.candidate import Candidate
from app.models.Screening import Screening
from app.models.user import User
from app.schemas.candidate import CandidateResponse


router = APIRouter(
    prefix="/candidates",
    tags=["Candidates"],
)


def get_current_hr_user(
    db: Session,
    current_user: str,
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

    return user


@router.get(
    "/screening/{screening_id}",
    response_model=list[CandidateResponse],
)
def list_screening_candidates(
    screening_id: int,
    processing_status: str | None = None,
    skill: str | None = None,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    user = get_current_hr_user(db, current_user)

    screening = (
        db.query(Screening)
        .filter(
            Screening.id == screening_id,
            Screening.created_by == user.id,
        )
        .first()
    )

    if screening is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Screening not found",
        )

    query = db.query(Candidate).filter(
        Candidate.screening_id == screening_id
    )

    if processing_status:
        normalized_status = processing_status.strip().upper()

        allowed_statuses = {
            "PENDING",
            "PROCESSED",
            "PROCESSING_FAILED",
        }

        if normalized_status not in allowed_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid processing status",
            )

        query = query.filter(
            Candidate.status == normalized_status
        )

    if skill:
        query = query.filter(
            Candidate.skills.ilike(f"%{skill.strip()}%")
        )

    return query.order_by(Candidate.id.asc()).all()


@router.get(
    "/{candidate_id}",
    response_model=CandidateResponse,
)
def get_candidate(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
):
    user = get_current_hr_user(db, current_user)

    candidate = (
        db.query(Candidate)
        .join(
            Screening,
            Candidate.screening_id == Screening.id,
        )
        .filter(
            Candidate.id == candidate_id,
            Screening.created_by == user.id,
        )
        .first()
    )

    if candidate is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidate not found",
        )

    return candidate