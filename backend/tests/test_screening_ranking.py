
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

def test_missing_eligibility_status_defaults_to_needs_review():
    matches = [
        {
            "candidate_id": 1,
            "overall_score": 90.0,
        },
        {
            "candidate_id": 2,
            "eligibility_status": "ELIGIBLE",
            "overall_score": 50.0,
        },
    ]

    ranked = rank_matches(matches)

    assert ranked[0]["candidate_id"] == 2
    assert ranked[1]["candidate_id"] == 1


def test_unknown_eligibility_status_defaults_to_needs_review():
    matches = [
        {
            "candidate_id": 1,
            "eligibility_status": "UNKNOWN_STATUS",
            "overall_score": 90.0,
        },
        {
            "candidate_id": 2,
            "eligibility_status": "NEEDS_REVIEW",
            "overall_score": 50.0,
        },
    ]

    ranked = rank_matches(matches)

    # Both have the same effective priority, so score breaks the tie.
    assert ranked[0]["candidate_id"] == 1
    assert ranked[1]["candidate_id"] == 2


def test_input_list_is_not_modified():
    matches = [
        {
            "candidate_id": 1,
            "eligibility_status": "NOT_ELIGIBLE",
            "overall_score": 95.0,
        },
        {
            "candidate_id": 2,
            "eligibility_status": "ELIGIBLE",
            "overall_score": 70.0,
        },
    ]
    original_order = [item["candidate_id"] for item in matches]

    rank_matches(matches)

    assert [item["candidate_id"] for item in matches] == original_order

import pytest


@pytest.mark.parametrize(
    "invalid_score",
    [None, "90", float("nan"), float("inf"), float("-inf"), True],
)
def test_invalid_overall_score_is_rejected(invalid_score):
    matches = [
        {
            "candidate_id": 1,
            "eligibility_status": "ELIGIBLE",
            "overall_score": invalid_score,
        },
        {
            "candidate_id": 2,
            "eligibility_status": "ELIGIBLE",
            "overall_score": 80.0,
        },
    ]

    with pytest.raises(ValueError):
        rank_matches(matches)


def test_missing_overall_score_is_rejected():
    matches = [
        {
            "candidate_id": 1,
            "eligibility_status": "ELIGIBLE",
        },
    ]

    with pytest.raises(ValueError):
        rank_matches(matches)


@pytest.mark.parametrize("invalid_score", [-1.0, 100.1])
def test_out_of_range_overall_score_is_rejected(invalid_score):
    matches = [
        {
            "candidate_id": 1,
            "eligibility_status": "ELIGIBLE",
            "overall_score": invalid_score,
        },
    ]

    with pytest.raises(ValueError):
        rank_matches(matches)

def test_equal_priority_and_score_preserves_input_order():
    matches = [
        {
            "candidate_id": 1,
            "eligibility_status": "ELIGIBLE",
            "overall_score": 85.0,
        },
        {
            "candidate_id": 2,
            "eligibility_status": "ELIGIBLE",
            "overall_score": 85.0,
        },
    ]

    ranked = rank_matches(matches)

    assert [item["candidate_id"] for item in ranked] == [1, 2]