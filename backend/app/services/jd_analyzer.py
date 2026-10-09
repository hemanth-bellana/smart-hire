from app.services.jd_parser import (
    extract_experience_requirement,
    extract_preferred_skills,
    extract_required_skills,
    extract_experience_areas,
    extract_education_requirements,
)


def analyze_job_description(text: str) -> dict:
    return {
        "required_skills": extract_required_skills(text),
        "preferred_skills": extract_preferred_skills(text),
        **extract_experience_requirement(text),
        "required_experience_areas": extract_experience_areas(text),
        "education_requirements": extract_education_requirements(text),
    }