from app.services.jd_parser import (
    extract_minimum_experience,
    extract_preferred_skills,
    extract_required_skills,
)


def analyze_job_description(text: str) -> dict:
    return {
        "required_skills": extract_required_skills(text),
        "preferred_skills": extract_preferred_skills(text),
        "minimum_experience_years": extract_minimum_experience(text),
    }