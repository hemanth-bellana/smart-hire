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
    Extract structured experience requirements from a JD.

    Supported formats include:
    - 0-3 years
    - 0 to 3 years
    - 3-5 years
    - 3+ years
    - minimum 3 years
    - at least 3 years
    - 3 years of experience
    """

    # Example:
    # 0-3 years
    # 0 - 3 years
    # 0 to 3 years
    range_pattern = (
        r"(\d+)\s*(?:-|–|—|to)\s*(\d+)\s*"
        r"(?:years?|yrs?)"
    )

    range_match = re.search(
        range_pattern,
        text,
        re.IGNORECASE,
    )

    if range_match:
        minimum_years = int(range_match.group(1))
        maximum_years = int(range_match.group(2))

        return {
            "minimum_experience_years": minimum_years,
            "maximum_experience_years": maximum_years,
            "experience_requirement_type": "RANGE",
        }

    # Example:
    # 3+ years
    # 5+ yrs
    plus_pattern = (
        r"(\d+)\+?\s*\+\s*"
        r"(?:years?|yrs?)"
    )

    plus_match = re.search(
        plus_pattern,
        text,
        re.IGNORECASE,
    )

    if plus_match:
        minimum_years = int(plus_match.group(1))

        return {
            "minimum_experience_years": minimum_years,
            "maximum_experience_years": None,
            "experience_requirement_type": "MINIMUM",
        }

    # Example:
    # minimum 3 years
    minimum_pattern = (
        r"(?:minimum\s+(?:of\s+)?|at\s+least\s+)"
        r"(\d+)\+?\s*"
        r"(?:years?|yrs?)"
    )

    minimum_match = re.search(
        minimum_pattern,
        text,
        re.IGNORECASE,
    )

    if minimum_match:
        minimum_years = int(minimum_match.group(1))

        return {
            "minimum_experience_years": minimum_years,
            "maximum_experience_years": None,
            "experience_requirement_type": "MINIMUM",
        }

    # Example:
    # 3 years of experience
    fixed_pattern = (
        r"(\d+)\s*"
        r"(?:years?|yrs?)\s+"
        r"(?:of\s+)?experience"
    )

    fixed_match = re.search(
        fixed_pattern,
        text,
        re.IGNORECASE,
    )

    if fixed_match:
        minimum_years = int(fixed_match.group(1))

        return {
            "minimum_experience_years": minimum_years,
            "maximum_experience_years": None,
            "experience_requirement_type": "MINIMUM",
        }

    return {
        "minimum_experience_years": None,
        "maximum_experience_years": None,
        "experience_requirement_type": "NONE",
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