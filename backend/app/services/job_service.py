from sqlalchemy.orm import Session

from app.repositories.job_repository import (
    create_job,
    get_job_by_id,
    get_jobs,
)
from app.schemas.job import JobCreate


def create_new_job(
    db: Session,
    job_data: JobCreate,
    created_by: int,
):
    return create_job(
        db=db,
        title=job_data.title,
        description=job_data.description,
        location=job_data.location,
        employment_type=job_data.employment_type,
        created_by=created_by,
    )


def get_user_jobs(
    db: Session,
    created_by: int,
):
    return get_jobs(
        db=db,
        created_by=created_by,
    )


def get_user_job(
    db: Session,
    job_id: int,
    created_by: int,
):
    return get_job_by_id(
        db=db,
        job_id=job_id,
        created_by=created_by,
    )