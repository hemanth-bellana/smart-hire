
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.screening_requirement_service import (
    analyze_and_save_screening_requirements,
)


def run_requirement_analysis(jd_text):
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    screening = SimpleNamespace(
        id=1,
        jd_text=jd_text,
    )

    result = analyze_and_save_screening_requirements(
        db=db,
        screening=screening,
    )

    return result, db


def test_saves_minimum_experience_requirement():
    result, db = run_requirement_analysis(
        "Python developer with at least 3 years of experience"
    )

    saved_requirement = db.add.call_args.args[0]

    assert saved_requirement.minimum_experience_years == 3
    assert saved_requirement.experience_requirement_type == "MINIMUM"
    assert saved_requirement.maximum_experience_years is None


def test_saves_experience_range():
    result, db = run_requirement_analysis(
        "Python developer with 2-4 years of experience"
    )

    saved_requirement = db.add.call_args.args[0]

    assert saved_requirement.minimum_experience_years == 2
    assert saved_requirement.maximum_experience_years == 4
    assert saved_requirement.experience_requirement_type == "RANGE"


def test_saves_no_experience_requirement():
    _, db = run_requirement_analysis(
        "We are looking for a Python developer with strong communication skills."
    )

    saved_requirement = db.add.call_args.args[0]

    assert saved_requirement.minimum_experience_years is None
    assert saved_requirement.maximum_experience_years is None
    assert saved_requirement.experience_requirement_type == "NONE"
