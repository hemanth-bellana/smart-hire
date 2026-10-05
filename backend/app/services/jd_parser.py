import re


KNOWN_SKILLS = [
    "Python",
    "Java",
    "Kotlin",
    "C",
    "C++",
    "JavaScript",
    "TypeScript",
    "SQL",
    "HTML",
    "CSS",
    "React",
    "React.js",
    "Node.js",
    "Spring Boot",
    "FastAPI",
    "Flask",
    "Django",
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
    "AWS",
    "Azure",
    "GCP",
    "Docker",
    "Kubernetes",
    "Git",
    "GitHub",
    "PostgreSQL",
    "MySQL",
    "MongoDB",
    "Redis",
]


def get_section(
    text: str,
    start_heading: str,
    end_headings: list[str],
) -> str:
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    start_index = None

    for index, line in enumerate(lines):
        if line.lower().rstrip(":") == start_heading.lower():
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
    found_skills = []

    for skill in KNOWN_SKILLS:
        pattern = rf"(?<!\w){re.escape(skill)}(?!\w)"

        if re.search(pattern, section_text, re.IGNORECASE):
            found_skills.append(skill)

    return found_skills


def extract_required_skills(text: str) -> list[str]:
    section = get_section(
        text,
        "Required Skills",
        ["Preferred Skills", "Experience", "Education"],
    )

    return extract_skills_from_section(section)


def extract_preferred_skills(text: str) -> list[str]:
    section = get_section(
        text,
        "Preferred Skills",
        ["Experience", "Education", "Required Skills"],
    )

    return extract_skills_from_section(section)


def extract_minimum_experience(text: str) -> int | None:
    patterns = [
        r"(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?experience",
        r"minimum\s+(?:of\s+)?(\d+)\+?\s*(?:years?|yrs?)",
        r"at\s+least\s+(\d+)\+?\s*(?:years?|yrs?)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            return int(match.group(1))

    return None