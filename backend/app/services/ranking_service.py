
def rank_matches(matches: list[dict]) -> list[dict]:
    """Rank candidates by eligibility, then by overall score."""

    eligibility_priority = {
        "ELIGIBLE": 0,
        "NEEDS_REVIEW": 1,
        "NOT_ELIGIBLE": 2,
    }

    return sorted(
        matches,
        key=lambda item: (
            eligibility_priority.get(
                item.get("eligibility_status", "NEEDS_REVIEW"),
                1,
            ),
            -item["overall_score"],
        ),
    )
