
import numpy as np

from app.services import semantic_matching_service as semantic_service


class FakeEmbeddingModel:
    def encode(self, texts, normalize_embeddings=True):
        assert normalize_embeddings is True
        assert len(texts) == 2

        return np.array([
            [1.0, 0.0],
            [1.0, 0.0],
        ])


def test_missing_resume_text_is_unavailable(monkeypatch):
    def fail_if_called():
        raise AssertionError("Model should not load for missing text.")

    monkeypatch.setattr(
        semantic_service,
        "load_embedding_model",
        fail_if_called,
    )

    result = semantic_service.calculate_semantic_match(
        candidate_resume_text="  ",
        job_description_text="Python developer",
    )

    assert result["semantic_score"] is None
    assert result["semantic_available"] is False
    assert "resume text is unavailable" in result["semantic_summary"]


def test_missing_job_description_is_unavailable(monkeypatch):
    def fail_if_called():
        raise AssertionError("Model should not load for missing text.")

    monkeypatch.setattr(
        semantic_service,
        "load_embedding_model",
        fail_if_called,
    )

    result = semantic_service.calculate_semantic_match(
        candidate_resume_text="Python developer",
        job_description_text=None,
    )

    assert result["semantic_score"] is None
    assert result["semantic_available"] is False
    assert "Job description text is unavailable" in result["semantic_summary"]


def test_successful_semantic_match_returns_score(monkeypatch):
    monkeypatch.setattr(
        semantic_service,
        "load_embedding_model",
        lambda: FakeEmbeddingModel(),
    )

    result = semantic_service.calculate_semantic_match(
        candidate_resume_text="Python developer",
        job_description_text="Python developer",
    )

    assert result["semantic_score"] == 100.0
    assert result["semantic_available"] is True
    assert "calculated successfully" in result["semantic_summary"]


def test_model_failure_marks_semantic_matching_unavailable(monkeypatch):
    def fail_to_load():
        raise RuntimeError("Simulated model loading failure")

    monkeypatch.setattr(
        semantic_service,
        "load_embedding_model",
        fail_to_load,
    )

    result = semantic_service.calculate_semantic_match(
        candidate_resume_text="Python developer",
        job_description_text="Python engineer",
    )

    assert result["semantic_score"] is None
    assert result["semantic_available"] is False
    assert "excluded from the overall score" in result["semantic_summary"]


def test_non_finite_similarity_is_unavailable(monkeypatch):
    class InvalidEmbeddingModel:
        def encode(self, texts, normalize_embeddings=True):
            return np.array([
                [np.nan, 0.0],
                [1.0, 0.0],
            ])

    monkeypatch.setattr(
        semantic_service,
        "load_embedding_model",
        lambda: InvalidEmbeddingModel(),
    )

    result = semantic_service.calculate_semantic_match(
        candidate_resume_text="Python developer",
        job_description_text="Python engineer",
    )

    assert result["semantic_score"] is None
    assert result["semantic_available"] is False
