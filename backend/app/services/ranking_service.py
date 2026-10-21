
import math
from numbers import Real


def rank_matches(matches: list[dict]) -> list[dict]:
    """Rank candidates by eligibility, then by overall score.

    Scores must be finite numeric values between 0 and 100.
    Invalid or missing scores raise ValueError.
    """

    eligibility_priority = {
        "ELIGIBLE": 0,
        "NEEDS_REVIEW": 1,
        "NOT_ELIGIBLE": 2,
    }

    def get_sort_key(item: dict) -> tuple[int, float]:
        if "overall_score" not in item:
            raise ValueError(
                "Candidate match is missing overall_score."
            )

        score = item["overall_score"]

        if (
            isinstance(score, bool)
            or not isinstance(score, Real)
            or not math.isfinite(score)
            or not 0 <= score <= 100
        ):
            raise ValueError(
                "overall_score must be a finite number "
                "between 0 and 100."
            )

        status = item.get("eligibility_status", "NEEDS_REVIEW")
        priority = eligibility_priority.get(status, 1)

        return priority, -score

    return sorted(matches, key=get_sort_key)
