from sqlalchemy.orm import Session

from app.models.Screening import Screening
from app.models.screening_requirement import ScreeningRequirement
from app.services.jd_analyzer import analyze_job_description


def analyze_and_save_screening_requirements(
    db: Session,
    screening: Screening,
) -> ScreeningRequirement:
    """
    Analyze a screening JD and save its structured requirements.

    If requirements already exist for the screening, they are updated.
    Otherwise, a new ScreeningRequirement record is created.
    """

    analysis = analyze_job_description(screening.jd_text)

    requirement = (
        db.query(ScreeningRequirement)
        .filter(
            ScreeningRequirement.screening_id == screening.id
        )
        .first()
    )

    if requirement is None:
        requirement = ScreeningRequirement(
            screening_id=screening.id,
        )
        db.add(requirement)

    requirement.required_skills = (
        ", ".join(analysis["required_skills"])
        if analysis["required_skills"]
        else None
    )

    requirement.preferred_skills = (
        ", ".join(analysis["preferred_skills"])
        if analysis["preferred_skills"]
        else None
    )

    requirement.minimum_experience_years = (
        analysis["minimum_experience_years"]
    )

    requirement.required_experience_areas = (
        ", ".join(analysis["required_experience_areas"])
        if analysis["required_experience_areas"]
        else None
    )

    requirement.education = (
        ", ".join(analysis["education_requirements"])
        if analysis["education_requirements"]
        else None
    )

    db.commit()
    db.refresh(requirement)

    return requirement