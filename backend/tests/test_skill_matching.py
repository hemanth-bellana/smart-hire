
from app.services.matching_service import calculate_skill_match


def test_required_skills_are_counted_only_once():
    result = calculate_skill_match(
        candidate_skills="Python",
        required_skills="Python, SQL, Python",
        preferred_skills=None,
    )

    assert result["skill_score"] == 50.0
    assert result["matched_required_skills"] == ["Python"]
    assert result["missing_required_skills"] == ["SQL"]


def test_preferred_skills_are_counted_only_once():
    result = calculate_skill_match(
        candidate_skills="Python",
        required_skills=None,
        preferred_skills="Python, SQL, Python",
    )

    assert result["skill_score"] == 50.0
    assert result["matched_preferred_skills"] == ["Python"]


def test_skill_matching_is_case_and_whitespace_insensitive():
    result = calculate_skill_match(
        candidate_skills=" python , SQL ",
        required_skills="Python, SQL",
        preferred_skills=None,
    )

    assert result["skill_score"] == 100.0
    assert result["matched_required_skills"] == ["Python", "SQL"]
    assert result["missing_required_skills"] == []


def test_required_and_preferred_weights_remain_80_20():
    result = calculate_skill_match(
        candidate_skills="Python",
        required_skills="Python, SQL",
        preferred_skills="Python, Docker",
    )

    # Required: 50% × 80% = 40
    # Preferred: 50% × 20% = 10
    assert result["skill_score"] == 50.0
