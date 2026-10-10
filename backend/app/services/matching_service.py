import re

from app.models.candidate import Candidate
from app.models.screening_requirement import ScreeningRequirement


# ============================================================
# Utility Functions
# ============================================================
from app.services.semantic_matching_service import (
    calculate_semantic_match,
)

def normalize_skill(skill: str) -> str:
    """
    Normalize a skill name for comparison.
    """
    return skill.strip().lower()


def parse_skill_string(skills: str | None) -> list[str]:
    """
    Convert a comma-separated string into a clean list.
    """
    if not skills:
        return []

    return [
        skill.strip()
        for skill in skills.split(",")
        if skill.strip()
    ]


# ============================================================
# Skill Matching
# ============================================================


def calculate_skill_match(
    candidate_skills: str | None,
    required_skills: str | None,
    preferred_skills: str | None,
) -> dict:
    """
    Compare candidate skills against required and preferred
    job-description skills.
    """

    candidate_skill_list = parse_skill_string(candidate_skills)
    required_skill_list = parse_skill_string(required_skills)
    preferred_skill_list = parse_skill_string(preferred_skills)

    candidate_normalized = {
        normalize_skill(skill)
        for skill in candidate_skill_list
    }

    matched_required = []
    missing_required = []

    for skill in required_skill_list:
        if normalize_skill(skill) in candidate_normalized:
            matched_required.append(skill)
        else:
            missing_required.append(skill)

    matched_preferred = []

    for skill in preferred_skill_list:
        if normalize_skill(skill) in candidate_normalized:
            matched_preferred.append(skill)

    required_score = (
        len(matched_required) / len(required_skill_list) * 100
        if required_skill_list
        else 100
    )

    preferred_score = (
        len(matched_preferred) / len(preferred_skill_list) * 100
        if preferred_skill_list
        else 100
    )

    if required_skill_list and preferred_skill_list:
        skill_score = (
            required_score * 0.8
            + preferred_score * 0.2
        )
    elif required_skill_list:
        skill_score = required_score
    elif preferred_skill_list:
        skill_score = preferred_score
    else:
        skill_score = 0

    return {
        "skill_score": round(skill_score, 2),
        "matched_required_skills": matched_required,
        "missing_required_skills": missing_required,
        "matched_preferred_skills": matched_preferred,
    }


# ============================================================
# Experience Matching
# ============================================================


def calculate_experience_match(
    candidate_experience_years: int | None,
    minimum_experience_years: int | None,
    maximum_experience_years: int | None = None,
    experience_requirement_type: str = "NONE",
) -> dict:
    """
    Compare candidate experience against the structured
    experience requirement from the job description.
    """

    requirement_type = experience_requirement_type.upper()

    if requirement_type == "NONE":
        return {
            "experience_score": 100.0,
            "experience_match": True,
            "experience_summary": (
                "No minimum experience requirement was specified."
            ),
        }

    if candidate_experience_years is None:
        return {
            "experience_score": 0.0,
            "experience_match": False,
            "experience_summary": (
                "Candidate experience could not be determined "
                "from the resume."
            ),
        }

    if requirement_type == "RANGE":
        if (
            minimum_experience_years is None
            or maximum_experience_years is None
        ):
            return {
                "experience_score": 0.0,
                "experience_match": False,
                "experience_summary": (
                    "The experience range in the job description "
                    "could not be determined."
                ),
            }

        if candidate_experience_years >= minimum_experience_years:
            return {
                "experience_score": 100.0,
                "experience_match": True,
                "experience_summary": (
                    f"Candidate has {candidate_experience_years} "
                    f"years of experience and meets the minimum "
                    f"requirement of {minimum_experience_years} "
                    f"years for the "
                    f"{minimum_experience_years}-"
                    f"{maximum_experience_years} year range."
                ),
            }

        return {
            "experience_score": 0.0,
            "experience_match": False,
            "experience_summary": (
                f"Candidate has {candidate_experience_years} "
                f"years of experience, but the role requires "
                f"at least {minimum_experience_years} years."
            ),
        }

    if requirement_type == "MINIMUM":
        if minimum_experience_years is None:
            return {
                "experience_score": 0.0,
                "experience_match": False,
                "experience_summary": (
                    "The minimum experience requirement could "
                    "not be determined."
                ),
            }

        if candidate_experience_years >= minimum_experience_years:
            return {
                "experience_score": 100.0,
                "experience_match": True,
                "experience_summary": (
                    f"Candidate has {candidate_experience_years} "
                    f"years of experience, meeting or exceeding "
                    f"the minimum requirement of "
                    f"{minimum_experience_years} years."
                ),
            }

        return {
            "experience_score": 0.0,
            "experience_match": False,
            "experience_summary": (
                f"Candidate has {candidate_experience_years} "
                f"years of experience, but the role requires "
                f"at least {minimum_experience_years} years."
            ),
        }

    return {
        "experience_score": 0.0,
        "experience_match": False,
        "experience_summary": (
            f"Unsupported experience requirement type: "
            f"{experience_requirement_type}."
        ),
    }


# ============================================================
# Education Matching
# ============================================================


def calculate_education_match(
    candidate_education: str | None,
    required_education: str | None,
) -> dict:
    """
    Compare candidate education against the education
    requirement from the job description.
    """

    if not required_education:
        return {
            "education_score": 100.0,
            "education_match": True,
            "education_summary": (
                "No specific education requirement was specified."
            ),
        }

    if not candidate_education:
        return {
            "education_score": 0.0,
            "education_match": False,
            "education_summary": (
                "Candidate education could not be determined "
                "from the resume."
            ),
        }

    candidate_education_normalized = candidate_education.lower()

    required_education_items = [
        item.strip()
        for item in required_education.split(",")
        if item.strip()
    ]

    matched_requirements = []

    for requirement in required_education_items:
        requirement_normalized = requirement.lower()

        if requirement_normalized in candidate_education_normalized:
            matched_requirements.append(requirement)

    if matched_requirements:
        return {
            "education_score": 100.0,
            "education_match": True,
            "education_summary": (
                "Candidate education satisfies the "
                "specified education requirement."
            ),
        }

    return {
        "education_score": 0.0,
        "education_match": False,
        "education_summary": (
            "Candidate education does not satisfy the "
            "specified education requirement."
        ),
    }


# ============================================================
# Certification Matching
# ============================================================


def calculate_certification_match(
    candidate_certifications: str | None,
    required_certifications: str | None,
) -> dict:
    """
    Compare candidate certifications against certifications
    required by the job description.
    """

    if not required_certifications:
        return {
            "certification_score": 100.0,
            "certification_match": True,
            "certification_summary": (
                "No specific certification requirement was specified."
            ),
            "matched_certifications": [],
            "missing_certifications": [],
        }

    if not candidate_certifications:
        required_list = parse_skill_string(
            required_certifications
        )

        return {
            "certification_score": 0.0,
            "certification_match": False,
            "certification_summary": (
                "Candidate certifications could not be "
                "determined from the resume."
            ),
            "matched_certifications": [],
            "missing_certifications": required_list,
        }

    candidate_certification_list = parse_skill_string(
        candidate_certifications
    )

    required_certification_list = parse_skill_string(
        required_certifications
    )

    candidate_normalized = {
        normalize_skill(certification)
        for certification in candidate_certification_list
    }

    matched_certifications = []
    missing_certifications = []

    for certification in required_certification_list:
        if normalize_skill(certification) in candidate_normalized:
            matched_certifications.append(certification)
        else:
            missing_certifications.append(certification)

    certification_score = (
        len(matched_certifications)
        / len(required_certification_list)
        * 100
        if required_certification_list
        else 100
    )

    certification_match = len(missing_certifications) == 0

    if certification_match:
        certification_summary = (
            "Candidate certifications satisfy the "
            "specified certification requirements."
        )
    else:
        certification_summary = (
            "Candidate is missing one or more required "
            "certifications."
        )

    return {
        "certification_score": round(
            certification_score,
            2,
        ),
        "certification_match": certification_match,
        "certification_summary": certification_summary,
        "matched_certifications": matched_certifications,
        "missing_certifications": missing_certifications,
    }


# ============================================================
# Keyword Matching
# ============================================================


STOP_WORDS = {
    "the",
    "and",
    "for",
    "with",
    "that",
    "this",
    "from",
    "are",
    "you",
    "your",
    "our",
    "will",
    "have",
    "has",
    "was",
    "were",
    "been",
    "being",
    "into",
    "their",
    "they",
    "them",
    "these",
    "those",
    "who",
    "what",
    "when",
    "where",
    "which",
    "while",
    "using",
    "used",
    "use",
    "work",
    "working",
    "build",
    "building",
    "develop",
    "developing",
    "development",
    "experience",
    "skills",
    "skill",
    "required",
    "preferred",
    "responsibilities",
    "responsibility",
    "candidate",
    "role",
    "job",
    "team",
    "teams",
    "application",
    "applications",
    "years",
    "year",
    "etc",
}


def extract_keywords(text: str | None) -> list[str]:
    """
    Extract meaningful single-word keywords from text.
    """

    if not text:
        return []

    words = re.findall(
        r"\b[a-zA-Z][a-zA-Z0-9+#.-]*\b",
        text.lower(),
    )

    keywords = []

    for word in words:
        cleaned_word = word.strip(".,;:()[]{}")

        if len(cleaned_word) < 3:
            continue

        if cleaned_word in STOP_WORDS:
            continue

        if cleaned_word not in keywords:
            keywords.append(cleaned_word)

    return keywords


def calculate_keyword_match(
    candidate_resume_text: str | None,
    job_description_text: str | None,
) -> dict:
    """
    Compare important keywords from the JD against the
    candidate's resume.
    """

    jd_keywords = extract_keywords(
        job_description_text
    )

    candidate_keywords = extract_keywords(
        candidate_resume_text
    )

    candidate_keyword_set = set(candidate_keywords)

    matched_keywords = []
    missing_keywords = []

    for keyword in jd_keywords:
        if keyword in candidate_keyword_set:
            matched_keywords.append(keyword)
        else:
            missing_keywords.append(keyword)

    if not jd_keywords:
        keyword_score = 100.0
        keyword_summary = (
            "No meaningful keywords could be extracted "
            "from the job description."
        )
    else:
        keyword_score = (
            len(matched_keywords)
            / len(jd_keywords)
            * 100
        )

        if matched_keywords:
            keyword_summary = (
                f"Candidate resume matches "
                f"{len(matched_keywords)} of "
                f"{len(jd_keywords)} meaningful JD keywords."
            )
        else:
            keyword_summary = (
                "Candidate resume does not contain the "
                "meaningful keywords identified from the JD."
            )

    return {
        "keyword_score": round(
            keyword_score,
            2,
        ),
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "keyword_summary": keyword_summary,
    }


# ============================================================
# Overall Score
# ============================================================


DEFAULT_WEIGHTS = {
    "skill": 40,
    "experience": 20,
    "semantic": 20,
    "education": 10,
    "certification": 5,
    "keyword": 5,
}


def validate_weights(weights: dict[str, float]) -> None:
    """
    Make sure scoring weights add up to exactly 100.
    """

    total = sum(weights.values())

    if round(total, 2) != 100:
        raise ValueError(
            f"Scoring weights must total 100. "
            f"Current total: {total}"
        )




def calculate_overall_score(
    skill_score: float,
    experience_score: float,
    semantic_score: float = 0.0,
    education_score: float = 0.0,
    certification_score: float = 0.0,
    keyword_score: float = 0.0,
    weights: dict[str, float] | None = None,
    applicable_components: set[str] | None = None,
) -> dict:
    """
    Calculate the weighted overall candidate score.

    When applicable_components is provided, redistribute the
    original weights across only the applicable components.
    """

    scoring_weights = (
        weights.copy()
        if weights is not None
        else DEFAULT_WEIGHTS.copy()
    )

    required_components = {
        "skill",
        "experience",
        "semantic",
        "education",
        "certification",
        "keyword",
    }

    if set(scoring_weights.keys()) != required_components:
        raise ValueError(
            "Weights must contain exactly these components: "
            "skill, experience, semantic, education, "
            "certification, keyword."
        )

    validate_weights(scoring_weights)

    component_scores = {
        "skill": skill_score,
        "experience": experience_score,
        "semantic": semantic_score,
        "education": education_score,
        "certification": certification_score,
        "keyword": keyword_score,
    }

    for component, score in component_scores.items():
        if not isinstance(score, (int, float)) or not 0 <= score <= 100:
            raise ValueError(
                f"{component} score must be between 0 and 100."
            )

    if applicable_components is None:
        applicable_components = required_components.copy()

    unknown_components = applicable_components - required_components
    if unknown_components:
        raise ValueError(
            f"Unknown scoring components: {sorted(unknown_components)}"
        )

    if not applicable_components:
        return {
            "overall_score": 0.0,
            "component_scores": {
                f"{component}_score": round(score, 2)
                for component, score in component_scores.items()
            },
            "weighted_scores": {
                component: 0.0
                for component in component_scores
            },
            "weights": {component: 0.0 for component in component_scores},
        }

    applicable_weight_total = sum(
        scoring_weights[component]
        for component in applicable_components
    )

    if applicable_weight_total <= 0:
        raise ValueError(
            "Applicable components must have a combined weight greater than zero."
        )

    normalized_weights = {
        component: (
            scoring_weights[component] * 100 / applicable_weight_total
            if component in applicable_components
            else 0.0
        )
        for component in component_scores
    }

    weighted_scores = {
        component: (
            component_scores[component] * normalized_weights[component] / 100
        )
        for component in component_scores
    }

    overall_score = sum(weighted_scores.values())

    return {
        "overall_score": round(overall_score, 2),
        "component_scores": {
            f"{component}_score": round(score, 2)
            for component, score in component_scores.items()
        },
        "weighted_scores": {
            component: round(score, 2)
            for component, score in weighted_scores.items()
        },
        "weights": {
            component: round(weight, 2)
            for component, weight in normalized_weights.items()
        },
    }


# ============================================================
# Candidate vs Screening
# ============================================================



def match_candidate_against_screening(
    candidate: Candidate,
    requirement: ScreeningRequirement,
    screening,
) -> dict:
    """
    Match one candidate against the structured requirements
    of a screening.
    """

    # ---------------------------------------------------------
    # Skill matching
    # ---------------------------------------------------------

    skill_result = calculate_skill_match(
        candidate_skills=candidate.skills,
        required_skills=requirement.required_skills,
        preferred_skills=requirement.preferred_skills,
    )

    # ---------------------------------------------------------
    # Experience matching
    # ---------------------------------------------------------

    experience_result = calculate_experience_match(
        candidate_experience_years=candidate.experience_years,
        minimum_experience_years=(
            requirement.minimum_experience_years
        ),
        maximum_experience_years=(
            requirement.maximum_experience_years
        ),
        experience_requirement_type=(
            requirement.experience_requirement_type
        ),
    )

    # ---------------------------------------------------------
    # Mandatory experience eligibility
    # ---------------------------------------------------------

    requirement_type = (
        (requirement.experience_requirement_type or "NONE")
        .strip()
        .upper()
    )

    minimum_years = requirement.minimum_experience_years
    maximum_years = requirement.maximum_experience_years

    if requirement_type == "NONE":
        eligibility_status = "ELIGIBLE"
        eligibility_reason = (
            "No mandatory experience requirement was specified."
        )

    elif requirement_type == "MINIMUM":
        if (
            minimum_years is None
            or candidate.experience_years is None
        ):
            eligibility_status = "NEEDS_REVIEW"
            eligibility_reason = experience_result[
                "experience_summary"
            ]

        elif candidate.experience_years < minimum_years:
            eligibility_status = "NOT_ELIGIBLE"
            eligibility_reason = experience_result[
                "experience_summary"
            ]

        else:
            eligibility_status = "ELIGIBLE"
            eligibility_reason = experience_result[
                "experience_summary"
            ]

    elif requirement_type == "RANGE":
        if (
            minimum_years is None
            or maximum_years is None
            or candidate.experience_years is None
        ):
            eligibility_status = "NEEDS_REVIEW"
            eligibility_reason = experience_result[
                "experience_summary"
            ]

        elif candidate.experience_years < minimum_years:
            eligibility_status = "NOT_ELIGIBLE"
            eligibility_reason = experience_result[
                "experience_summary"
            ]

        else:
            eligibility_status = "ELIGIBLE"
            eligibility_reason = experience_result[
                "experience_summary"
            ]

    else:
        eligibility_status = "NEEDS_REVIEW"
        eligibility_reason = (
            "The experience requirement could not be evaluated."
        )

    # ---------------------------------------------------------
    # Education matching
    # ---------------------------------------------------------

    education_result = calculate_education_match(
        candidate_education=candidate.education,
        required_education=requirement.education,
    )

    # ---------------------------------------------------------
    # Certification matching
    # ---------------------------------------------------------

    required_certifications = getattr(
        requirement,
        "required_certifications",
        None,
    )

    certification_result = calculate_certification_match(
        candidate_certifications=candidate.certifications,
        required_certifications=required_certifications,
    )

    # ---------------------------------------------------------
    # Keyword matching
    # ---------------------------------------------------------

    keyword_result = calculate_keyword_match(
        candidate_resume_text=candidate.resume_text,
        job_description_text=screening.jd_text,
    )

    # ---------------------------------------------------------
    # Semantic matching
    # ---------------------------------------------------------

    semantic_result = calculate_semantic_match(
        candidate_resume_text=candidate.resume_text,
        job_description_text=screening.jd_text,
    )

    semantic_score = semantic_result["semantic_score"]

    # ---------------------------------------------------------
    # Overall score
    # ---------------------------------------------------------
    # ---------------------------------------------------------
    # Determine applicable scoring components
    # ---------------------------------------------------------

    applicable_components = set()

    if (
        requirement.required_skills
        or requirement.preferred_skills
    ):
        applicable_components.add("skill")

    requirement_type = (
        (requirement.experience_requirement_type or "NONE")
        .strip()
        .upper()
    )

    if requirement_type in {"MINIMUM", "RANGE"}:
        applicable_components.add("experience")

    if requirement.education and requirement.education.strip():
        applicable_components.add("education")

    if required_certifications and required_certifications.strip():
        applicable_components.add("certification")

    if (
        candidate.resume_text
        and candidate.resume_text.strip()
        and screening.jd_text
        and screening.jd_text.strip()
    ):
        applicable_components.add("semantic")

    if keyword_result["matched_keywords"] or keyword_result["missing_keywords"]:
        applicable_components.add("keyword")

    # ---------------------------------------------------------
    # Calculate the normalized overall score
    # ---------------------------------------------------------

    overall_result = calculate_overall_score(
        skill_score=skill_result["skill_score"],
        experience_score=experience_result["experience_score"],
        semantic_score=semantic_score,
        education_score=education_result["education_score"],
        certification_score=certification_result["certification_score"],
        keyword_score=keyword_result["keyword_score"],
        applicable_components=applicable_components,
    )


    # ---------------------------------------------------------
    # Final explainable result
    # ---------------------------------------------------------

    return {
        "candidate_id": candidate.id,
        "overall_score": overall_result["overall_score"],
        "skill_score": skill_result["skill_score"],
        "experience_score": experience_result["experience_score"],
        "semantic_score": semantic_score,
        "semantic_summary": semantic_result["semantic_summary"],
        "education_score": education_result["education_score"],
        "certification_score": certification_result[
            "certification_score"
        ],
        "keyword_score": keyword_result["keyword_score"],
        "matched_required_skills": skill_result[
            "matched_required_skills"
        ],
        "missing_required_skills": skill_result[
            "missing_required_skills"
        ],
        "matched_preferred_skills": skill_result[
            "matched_preferred_skills"
        ],
        "experience_match": experience_result["experience_match"],
        "experience_summary": experience_result[
            "experience_summary"
        ],
        "eligibility_status": eligibility_status,
        "eligibility_reason": eligibility_reason,
        "education_match": education_result["education_match"],
        "education_summary": education_result["education_summary"],
        "certification_match": certification_result[
            "certification_match"
        ],
        "certification_summary": certification_result[
            "certification_summary"
        ],
        "matched_certifications": certification_result[
            "matched_certifications"
        ],
        "missing_certifications": certification_result[
            "missing_certifications"
        ],
        "matched_keywords": keyword_result["matched_keywords"],
        "missing_keywords": keyword_result["missing_keywords"],
        "keyword_summary": keyword_result["keyword_summary"],
        "scoring_weights": overall_result["weights"],
    }

from types import SimpleNamespace

from app.services.matching_service import match_candidate_against_screening


def make_candidate(experience_years):
    return SimpleNamespace(
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
