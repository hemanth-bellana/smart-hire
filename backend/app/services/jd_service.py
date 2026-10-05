from sqlalchemy.orm import Session

from app.models.job import Job
from app.models.requirement import JobRequirement
from app.services.jd_analyzer import analyze_job_description


def analyze_and_save_job_requirements(
    db: Session,
    job: Job,
) -> JobRequirement:
    analysis = analyze_job_description(job.description)

    requirement = JobRequirement(
        job_id=job.id,
        required_skills=(
            ", ".join(analysis["required_skills"])
            if analysis["required_skills"]
            else None
        ),
        preferred_skills=(
            ", ".join(analysis["preferred_skills"])
            if analysis["preferred_skills"]
            else None
        ),
        minimum_experience_years=analysis[
            "minimum_experience_years"
        ],
    )

    db.add(requirement)
    db.commit()
    db.refresh(requirement)

    return requirement