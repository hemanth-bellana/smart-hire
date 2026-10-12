import re
from app.services.jd_parser import extract_experience_requirement


def extract_experience_requirement(text: str) -> dict:
    """
    Extract experience requirements from a job description.

    Returns INVALID when a range is reversed or when distinct
    experience requirements conflict.
    """

    def invalid_requirement() -> dict:
        return {
            "minimum_experience_years": None,
            "maximum_experience_years": None,
            "experience_requirement_type": "INVALID",
        }

    candidates = []
    range_spans = []

    # Extract ranges such as 2-4 years or 2 to 4 years.
    range_pattern = (
        r"(?<!\w)(\d+)\s*(?:-|–|—|to)\s*(\d+)\s*"
        r"(?:years?|yrs?)\b"
    )

    for match in re.finditer(
        range_pattern, text, re.IGNORECASE
    ):
        minimum = int(match.group(1))
        maximum = int(match.group(2))
        range_spans.append(match.span())

        if minimum > maximum:
            return invalid_requirement()

        candidates.append(
            (minimum, maximum, "RANGE")
        )

    def inside_range(start: int) -> bool:
        return any(
            left <= start < right
            for left, right in range_spans
        )

    # Extract minimum requirements such as 3+ years.
    plus_pattern = (
        r"(?<!\w)(\d+)\s*\+\s*(?:years?|yrs?)\b"
    )

    for match in re.finditer(
        plus_pattern, text, re.IGNORECASE
    ):
        if not inside_range(match.start()):
            candidates.append(
                (int(match.group(1)), None, "MINIMUM")
            )

    # Extract phrases such as "at least 3 years".
    minimum_pattern = (
        r"(?:minimum\s+(?:of\s+)?|at\s+least\s+)"
        r"(\d+)\s*\+?\s*(?:years?|yrs?)\b"
    )

    for match in re.finditer(
        minimum_pattern, text, re.IGNORECASE
    ):
        if not inside_range(match.start()):
            candidates.append(
                (int(match.group(1)), None, "MINIMUM")
            )

    # Extract phrases such as "3 years of experience".
    fixed_pattern = (
        r"(?<!\w)(\d+)\s*(?:years?|yrs?)\s+"
        r"(?:of\s+)?experience\b"
    )

    for match in re.finditer(
        fixed_pattern, text, re.IGNORECASE
    ):
        if not inside_range(match.start()):
            candidates.append(
                (int(match.group(1)), None, "MINIMUM")
            )

    # Remove duplicate detections of the same requirement.
    candidates = list(dict.fromkeys(candidates))

    if not candidates:
        return {
            "minimum_experience_years": None,
            "maximum_experience_years": None,
            "experience_requirement_type": "NONE",
        }

    # Do not silently choose one when requirements conflict.
    if len(candidates) > 1:
        return invalid_requirement()

    minimum, maximum, requirement_type = candidates[0]

    return {
        "minimum_experience_years": minimum,
        "maximum_experience_years": maximum,
        "experience_requirement_type": requirement_type,
    }



def test_flags_reversed_experience_range():
    result = extract_experience_requirement(
        "The role requires 5-3 years of experience."
    )

    assert result["experience_requirement_type"] == "INVALID"


def test_flags_conflicting_experience_requirements():
    result = extract_experience_requirement(
        "The role requires at least 3 years of experience. "
        "Another section says 5-7 years of experience is required."
    )

    assert result["experience_requirement_type"] == "INVALID"


def test_no_experience_requirement_returns_none():
    result = extract_experience_requirement(
        "We are looking for a Python developer with strong communication skills."
    )

    assert result["minimum_experience_years"] is None
    assert result["maximum_experience_years"] is None
    assert result["experience_requirement_type"] == "NONE"

def test_extracts_valid_experience_range():
    result = extract_experience_requirement(
        "The role requires 2-4 years of experience."
    )

    assert result["minimum_experience_years"] == 2
    assert result["maximum_experience_years"] == 4
    assert result["experience_requirement_type"] == "RANGE"

def test_extracts_plus_years_requirement():
    result = extract_experience_requirement(
        "The role requires 3+ years of experience."
    )

    assert result["minimum_experience_years"] == 3
    assert result["maximum_experience_years"] is None
    assert result["experience_requirement_type"] == "MINIMUM"


def test_extracts_at_least_years_requirement():
    result = extract_experience_requirement(
        "Candidates must have at least 3 years of experience."
    )

    assert result["minimum_experience_years"] == 3
    assert result["maximum_experience_years"] is None
    assert result["experience_requirement_type"] == "MINIMUM"


def test_extracts_fixed_years_requirement():
    result = extract_experience_requirement(
        "Candidates need 3 years of experience."
    )

    assert result["minimum_experience_years"] == 3
    assert result["maximum_experience_years"] is None
    assert result["experience_requirement_type"] == "MINIMUM"
