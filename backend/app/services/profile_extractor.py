import re


def get_section(text: str, start_heading: str, end_headings: list[str]) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    start_index = None

    for index, line in enumerate(lines):
        if line.lower() == start_heading.lower():
            start_index = index + 1
            break

    if start_index is None:
        return ""

    end_index = len(lines)

    for index in range(start_index, len(lines)):
        if lines[index].lower() in [heading.lower() for heading in end_headings]:
            end_index = index
            break

    return "\n".join(lines[start_index:end_index])


def extract_education(text: str) -> str | None:
    education_section = get_section(
        text,
        "EDUCATION",
        ["SKILLS", "EXPERIENCE", "PROJECTS", "CERTIFICATIONS"],
    )

    if not education_section:
        return None

    return education_section


def extract_experience_years(text: str) -> float | None:
    experience_section = get_section(
        text,
        "EXPERIENCE",
        ["EDUCATION", "SKILLS", "PROJECTS", "CERTIFICATIONS"],
    )

    if not experience_section:
        return None

    patterns = [
        r"(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience",
        r"experience\s*[:\-]?\s*(\d+(?:\.\d+)?)\+?\s*(?:years?|yrs?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, experience_section, re.IGNORECASE)

        if match:
            return float(match.group(1))

    return None


def extract_previous_companies(text: str) -> list[str]:
    experience_section = get_section(
        text,
        "EXPERIENCE",
        ["EDUCATION", "SKILLS", "PROJECTS", "CERTIFICATIONS"],
    )

    if not experience_section:
        return []

    return []


def extract_certifications(text: str) -> list[str]:
    certifications_section = get_section(
        text,
        "CERTIFICATIONS",
        ["EDUCATION", "SKILLS", "EXPERIENCE", "PROJECTS"],
    )

    if not certifications_section:
        return []

    certifications = []

    for line in certifications_section.splitlines():
        line = line.strip()

        if line.startswith(""):
            line = line[1:].strip()

        if line:
            certifications.append(line)

    return certifications