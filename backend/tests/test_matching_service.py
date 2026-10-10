
from app.services.matching_service import calculate_experience_match


def test_candidate_meets_minimum_experience():
    result = calculate_experience_match(
        candidate_experience_years=3,
        minimum_experience_years=2,
        experience_requirement_type="MINIMUM",
    )

    assert result["experience_match"] is True
    assert result["experience_score"] == 100.0


def test_candidate_does_not_meet_minimum_experience():
    result = calculate_experience_match(
        candidate_experience_years=1,
        minimum_experience_years=2,
        experience_requirement_type="MINIMUM",
    )

    assert result["experience_match"] is False
    assert result["experience_score"] == 0.0


def test_missing_candidate_experience():
    result = calculate_experience_match(
        candidate_experience_years=None,
        minimum_experience_years=2,
        experience_requirement_type="MINIMUM",
    )

    assert result["experience_match"] is False
    assert result["experience_score"] == 0.0
    assert "could not be determined" in result["experience_summary"]


def test_no_experience_requirement():
    result = calculate_experience_match(
        candidate_experience_years=None,
        minimum_experience_years=None,
        experience_requirement_type="NONE",
    )

    assert result["experience_match"] is True
    assert result["experience_score"] == 100.0


from types import SimpleNamespace

from app.services.matching_service import match_candidate_against_screening



def make_candidate(experience_years):
    return SimpleNamespace(
        id=1,
        skills="Python, SQL",
        experience_years=experience_years,
        education="B.Tech",
        certifications=None,
        resume_text="Python developer with SQL experience",
    )


def make_requirement(
    requirement_type="MINIMUM",
    minimum_years=2,
    maximum_years=None,
):
    return SimpleNamespace(
        required_skills="Python",
        preferred_skills=None,
        minimum_experience_years=minimum_years,
        maximum_experience_years=maximum_years,
        experience_requirement_type=requirement_type,
        required_experience_areas=None,
        education=None,
        required_certifications=None,
    )


def make_screening():
    return SimpleNamespace(
        jd_text="Python developer with at least 2 years of experience"
    )

def test_candidate_is_eligible_when_experience_meets_minimum():
    candidate = make_candidate(experience_years=3)
    requirement = make_requirement(
        requirement_type="MINIMUM",
        minimum_years=2,
    )
    screening = make_screening()

    result = match_candidate_against_screening(
        candidate,
        requirement,
        screening,
    )

    assert result["eligibility_status"] == "ELIGIBLE"


def test_candidate_is_not_eligible_when_below_minimum_experience():
    candidate = make_candidate(experience_years=1)
    requirement = make_requirement(
        requirement_type="MINIMUM",
        minimum_years=2,
    )
    screening = make_screening()

    result = match_candidate_against_screening(
        candidate,
        requirement,
        screening,
    )

    assert result["eligibility_status"] == "NOT_ELIGIBLE"
    assert "requires at least 2 years" in result["eligibility_reason"]


def test_candidate_needs_review_when_experience_is_missing():
    candidate = make_candidate(experience_years=None)
    requirement = make_requirement(
        requirement_type="MINIMUM",
        minimum_years=2,
    )
    screening = make_screening()

    result = match_candidate_against_screening(
        candidate,
        requirement,
        screening,
    )

    assert result["eligibility_status"] == "NEEDS_REVIEW"
    assert "could not be determined" in result["eligibility_reason"]
