
from app.services.ranking_service import rank_matches


def test_eligible_candidate_ranks_before_candidate_needing_review():
    matches = [
        {
            "candidate_id": 1,
            "eligibility_status": "NEEDS_REVIEW",
            "overall_score": 95.0,
        },
        {
            "candidate_id": 2,
            "eligibility_status": "ELIGIBLE",
            "overall_score": 70.0,
        },
    ]

    ranked = rank_matches(matches)

    assert ranked[0]["candidate_id"] == 2
    assert ranked[1]["candidate_id"] == 1


def test_higher_scoring_eligible_candidate_ranks_first():
    matches = [
        {
            "candidate_id": 1,
            "eligibility_status": "ELIGIBLE",
            "overall_score": 65.0,
        },
        {
            "candidate_id": 2,
            "eligibility_status": "ELIGIBLE",
            "overall_score": 90.0,
        },
    ]

    ranked = rank_matches(matches)

    assert ranked[0]["candidate_id"] == 2
    assert ranked[1]["candidate_id"] == 1


def test_candidate_needing_review_ranks_before_ineligible_candidate():
    matches = [
        {
            "candidate_id": 1,
            "eligibility_status": "NOT_ELIGIBLE",
            "overall_score": 95.0,
        },
        {
            "candidate_id": 2,
            "eligibility_status": "NEEDS_REVIEW",
            "overall_score": 40.0,
        },
    ]

    ranked = rank_matches(matches)

    assert ranked[0]["candidate_id"] == 2
    assert ranked[1]["candidate_id"] == 1
