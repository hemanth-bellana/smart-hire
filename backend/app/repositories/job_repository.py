from sqlalchemy.orm import Session

from app.models.job import Job


def create_job(
    db: Session,
    title: str,
    description: str,
    location: str | None,
    employment_type: str | None,
    created_by: int,
) -> Job:
    job = Job(
        title=title,
        description=description,
        location=location,
        employment_type=employment_type,
        created_by=created_by,
    )

    db.add(job)
    db.commit()
    db.refresh(job)

    return job


def get_jobs(
    db: Session,
    created_by: int,
) -> list[Job]:
    return (
        db.query(Job)
        .filter(Job.created_by == created_by)
        .order_by(Job.created_at.desc())
        .all()
    )


def get_job_by_id(
    db: Session,
    job_id: int,
    created_by: int,
) -> Job | None:
    return (
        db.query(Job)
        .filter(
            Job.id == job_id,
            Job.created_by == created_by,
        )
        .first()
    )