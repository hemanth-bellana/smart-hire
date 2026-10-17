
from app.services.matching_service import (
    calculate_keyword_match,
    extract_keywords,
)


def test_extract_keywords_preserves_common_technical_terms():
    keywords = extract_keywords(
        "C++ C# .NET CI/CD Node.js Python"
    )

    assert "c++" in keywords
    assert "c#" in keywords
    assert ".net" in keywords
    assert "ci/cd" in keywords
    assert "node.js" in keywords
    assert "python" in keywords


def test_extract_keywords_handles_case_and_duplicates():
    keywords = extract_keywords(
        "Python PYTHON python Node.js NODE.JS"
    )

    assert keywords.count("python") == 1
    assert keywords.count("node.js") == 1


def test_keyword_match_recognizes_technical_terms():
    result = calculate_keyword_match(
        candidate_resume_text=(
            "Experienced in C++, C#, .NET, CI/CD and Node.js"
        ),
        job_description_text=(
            "Required: C++, C#, .NET, CI/CD and Node.js"
        ),
    )

    assert result["keyword_score"] == 100.0
    assert result["missing_keywords"] == []
    assert {
        "c++",
        "c#",
        ".net",
        "ci/cd",
        "node.js",
    }.issubset(set(result["matched_keywords"]))
