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


def extract_skills(text: str) -> list[str]:
    found_skills = []

    for skill in KNOWN_SKILLS:
        pattern = rf"(?<!\w){re.escape(skill)}(?!\w)"

        if re.search(pattern, text, re.IGNORECASE):
            found_skills.append(skill)

    return found_skills