import re


KNOWN_SKILLS = [
    # Programming languages
    "Python",
    "Java",
    "Kotlin",
    "C",
    "C++",
    "C#",
    "JavaScript",
    "TypeScript",
    "SQL",
    "PL/SQL",

    # Web
    "HTML",
    "CSS",
    "React",
    "React.js",
    "Node.js",
    "ASP.NET",
    "AJAX",
    "Silverlight",

    # Backend frameworks
    "Spring Boot",
    "FastAPI",
    "Flask",
    "Django",
    "WCF",
    "Windows Workflow",

    # AI / ML
    "Machine Learning",
    "Deep Learning",
    "Artificial Intelligence",
    "Generative AI",
    "NLP",
    "Natural Language Processing",
    "RAG",
    "LLM",
    "LangChain",
    "LangGraph",
    "TensorFlow",
    "PyTorch",
    "Scikit-learn",
    "Pandas",
    "NumPy",

    # Cloud / DevOps
    "AWS",
    "Azure",
    "GCP",
    "Docker",
    "Kubernetes",

    # Databases
    "PostgreSQL",
    "MySQL",
    "Microsoft SQL Server",
    "SQL Server",
    "MongoDB",
    "Oracle",
    "Redis",

    # Version control
    "Git",
    "GitHub",
]


def get_section(
    text: str,
    start_heading: str,
    end_headings: list[str],
) -> str:
    """
    Extract text between a section heading and the next known heading.
    """

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    start_index = None

    for index, line in enumerate(lines):
        normalized_line = line.lower().rstrip(":")

        if normalized_line == start_heading.lower():
            start_index = index + 1
            break

    if start_index is None:
        return ""

    end_index = len(lines)

    normalized_end_headings = {
        heading.lower()
        for heading in end_headings
    }

    for index in range(start_index, len(lines)):
        normalized_line = lines[index].lower().rstrip(":")

        if normalized_line in normalized_end_headings:
            end_index = index
            break

    return "\n".join(lines[start_index:end_index])


def extract_skills_from_section(section_text: str) -> list[str]:
    """
    Extract known skills from a section.
    """

    found_skills = []

    for skill in KNOWN_SKILLS:
        pattern = rf"(?<!\w){re.escape(skill)}(?!\w)"

        if re.search(
            pattern,
            section_text,
            re.IGNORECASE,
        ):
            found_skills.append(skill)

    return found_skills


def extract_required_skills(text: str) -> list[str]:
    """
    Extract required skills.

    Supports both structured JDs with a
    'Required Skills' section and JDs that
    use a 'Qualifications' section.
    """

    section = get_section(
        text,
        "Required Skills",
        [
            "Preferred Skills",
            "Experience",
            "Education",
            "Qualifications",
            "Responsibilities",
        ],
    )

    if section:
        return extract_skills_from_section(section)

    # Fallback for JDs that use Qualifications.
    qualifications = get_section(
        text,
        "Qualifications",
        [
            "Preferred Qualifications",
            "Preferred Skills",
            "Experience",
            "Responsibilities",
            "Education",
        ],
    )

    if qualifications:
        return extract_skills_from_section(
            qualifications
        )

    return []


def extract_preferred_skills(text: str) -> list[str]:
    """
    Extract preferred skills.
    """

    section = get_section(
        text,
        "Preferred Skills",
        [
            "Experience",
            "Education",
            "Required Skills",
            "Qualifications",
        ],
    )

    if section:
        return extract_skills_from_section(section)

    preferred_section = get_section(
        text,
        "Preferred Qualifications",
        [
            "Experience",
            "Education",
            "Required Skills",
            "Qualifications",
        ],
    )

    if preferred_section:
        return extract_skills_from_section(
            preferred_section
        )

    return []

def extract_experience_requirement(text: str) -> dict:
    """
    Extract experience requirements from a job description.

    Return INVALID for reversed ranges or conflicting requirements.
    """

    def invalid_requirement() -> dict:
        return {
            "minimum_experience_years": None,
            "maximum_experience_years": None,
            "experience_requirement_type": "INVALID",
        }

    candidates = []
    range_spans = []

    # Extract ranges such as 2-4 years and 2 to 4 years.
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

        candidates.append((minimum, maximum, "RANGE"))

    def inside_range(start: int) -> bool:
        return any(
            left <= start < right
            for left, right in range_spans
        )

    # Extract requirements such as 3+ years.
    plus_pattern = r"(?<!\w)(\d+)\s*\+\s*(?:years?|yrs?)\b"

    for match in re.finditer(
        plus_pattern, text, re.IGNORECASE
    ):
        if not inside_range(match.start()):
            candidates.append(
                (int(match.group(1)), None, "MINIMUM")
            )

    # Extract "minimum 3 years" and "at least 3 years".
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

    # Extract "3 years of experience".
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

    # Avoid silently selecting one of several requirements.
    if len(candidates) > 1:
        return invalid_requirement()

    minimum, maximum, requirement_type = candidates[0]

    return {
        "minimum_experience_years": minimum,
        "maximum_experience_years": maximum,
        "experience_requirement_type": requirement_type,
    }

def extract_experience_areas(
    text: str,
) -> list[str]:
    """
    Extract areas where the JD explicitly mentions experience.
    """

    experience_areas = []

    patterns = [
        r"experience with ([^.]+)",
        r"experience in ([^.]+)",
        r"hands[- ]on experience with ([^.]+)",
        r"hands[- ]on experience in ([^.]+)",
        r"experience developing ([^.]+)",
        r"experience building ([^.]+)",
    ]

    for pattern in patterns:
        matches = re.findall(
            pattern,
            text,
            re.IGNORECASE,
        )

        for match in matches:
            cleaned = match.strip()

            cleaned = re.sub(
                r"\s+(is|are)\s+"
                r"(required|preferred|mandatory).*$",
                "",
                cleaned,
                flags=re.IGNORECASE,
            )

            if cleaned:
                experience_areas.append(cleaned)

    unique_areas = []

    for area in experience_areas:
        if area not in unique_areas:
            unique_areas.append(area)

    return unique_areas


def extract_education_requirements(
    text: str,
) -> list[str]:
    """
    Extract common education requirements.
    """

    education_keywords = [
        "Bachelor's degree",
        "Bachelor's",
        "B.Tech",
        "B.E.",
        "B.E",
        "B.Sc",
        "BCA",
        "Master's degree",
        "Master's",
        "M.Tech",
        "M.E.",
        "M.E",
        "M.Sc",
        "MCA",
        "Ph.D.",
        "PhD",
    ]

    found_education = []

    for education in education_keywords:
        pattern = rf"(?<!\w){re.escape(education)}(?!\w)"

        if re.search(
            pattern,
            text,
            re.IGNORECASE,
        ):
            found_education.append(education)

    return found_education