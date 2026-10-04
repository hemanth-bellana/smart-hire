from app.services.candidate_extractor import (
    extract_email,
    extract_location,
    extract_name,
    extract_phone,
)
from app.services.profile_extractor import (
    extract_certifications,
    extract_education,
    extract_experience_years,
    extract_previous_companies,
)
from app.services.skill_extractor import extract_skills


def extract_candidate_profile(text: str) -> dict:
    return {
        "name": extract_name(text),
        "email": extract_email(text),
        "phone": extract_phone(text),
        "location": extract_location(text),
        "skills": extract_skills(text),
        "education": extract_education(text),
        "experience_years": extract_experience_years(text),
        "previous_companies": extract_previous_companies(text),
        "certifications": extract_certifications(text),
    }