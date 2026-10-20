
import pytest

from app.services.matching_service import (
    DEFAULT_WEIGHTS,
    calculate_overall_score,
    validate_weights,
)


def test_default_weights_total_100():
    assert sum(DEFAULT_WEIGHTS.values()) == 100


def test_default_weights_contain_all_six_components():
    assert set(DEFAULT_WEIGHTS) == {
        "skill",
        "experience",
        "semantic",
        "education",
        "certification",
        "keyword",
    }


def test_applicable_weights_are_normalized_to_100():
    result = calculate_overall_score(
        skill_score=80,
        experience_score=50,
        applicable_components={"skill", "experience"},
    )

    assert sum(result["weights"].values()) == pytest.approx(100)
    assert result["weights"]["skill"] == pytest.approx(66.67)
    assert result["weights"]["experience"] == pytest.approx(33.33)


def test_non_applicable_components_receive_zero_weight():
    result = calculate_overall_score(
        skill_score=80,
        experience_score=50,
        applicable_components={"skill", "experience"},
    )

    assert result["weights"]["education"] == 0
    assert result["weights"]["certification"] == 0
    assert result["weights"]["semantic"] == 0
    assert result["weights"]["keyword"] == 0


def test_overall_score_uses_normalized_weights():
    result = calculate_overall_score(
        skill_score=80,
        experience_score=50,
        applicable_components={"skill", "experience"},
    )

    # Original weights are 40 and 20.
    # Normalized weights become 66.67% and 33.33%.
    # Expected score: (80 * 2/3) + (50 * 1/3) = 70.
    assert result["overall_score"] == pytest.approx(70.0)


def test_all_components_applicable_preserves_default_weights():
    result = calculate_overall_score(
        skill_score=80,
        experience_score=70,
        semantic_score=90,
        education_score=60,
        certification_score=50,
        keyword_score=40,
    )

    assert result["weights"] == DEFAULT_WEIGHTS
    assert result["overall_score"] == pytest.approx(74.5)


def test_no_applicable_components_returns_zero_score():
    result = calculate_overall_score(
        skill_score=80,
        experience_score=50,
        applicable_components=set(),
    )

    assert result["overall_score"] == 0.0
    assert all(weight == 0 for weight in result["weights"].values())


def test_validate_weights_rejects_total_other_than_100():
    invalid_weights = DEFAULT_WEIGHTS.copy()
    invalid_weights["skill"] = 35

    with pytest.raises(ValueError, match="must total 100"):
        validate_weights(invalid_weights)


def test_calculate_overall_score_rejects_incomplete_weights():
    invalid_weights = DEFAULT_WEIGHTS.copy()
    invalid_weights.pop("keyword")

    with pytest.raises(ValueError, match="exactly these components"):
        calculate_overall_score(
            skill_score=80,
            experience_score=70,
            weights=invalid_weights,
        )


def test_calculate_overall_score_rejects_score_above_100():
    with pytest.raises(ValueError, match="between 0 and 100"):
        calculate_overall_score(
            skill_score=101,
            experience_score=70,
        )


def test_calculate_overall_score_rejects_negative_score():
    with pytest.raises(ValueError, match="between 0 and 100"):
        calculate_overall_score(
            skill_score=80,
            experience_score=-1,
        )

@pytest.mark.parametrize(
    "invalid_value",
    [
        -5,
        float("nan"),
        float("inf"),
        float("-inf"),
        "40",
        None,
    ],
)
def test_validate_weights_rejects_invalid_weight_values(invalid_value):
    invalid_weights = DEFAULT_WEIGHTS.copy()
    invalid_weights["skill"] = invalid_value

    with pytest.raises(ValueError):
        validate_weights(invalid_weights)


def test_validate_weights_rejects_negative_weight_even_when_total_is_100():
    invalid_weights = DEFAULT_WEIGHTS.copy()
    invalid_weights["skill"] = -10
    invalid_weights["experience"] = 70

    with pytest.raises(ValueError, match="non-negative"):
        validate_weights(invalid_weights)


@pytest.mark.parametrize("invalid_score", [True, False])
def test_calculate_overall_score_rejects_boolean_scores(invalid_score):
    with pytest.raises(ValueError, match="between 0 and 100"):
        calculate_overall_score(
            skill_score=invalid_score,
            experience_score=70,
        )