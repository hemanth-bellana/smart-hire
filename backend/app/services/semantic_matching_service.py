
import logging
import math
from functools import lru_cache

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


logger = logging.getLogger(__name__)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def load_embedding_model() -> SentenceTransformer:
    """
    Load the embedding model once and reuse it.
    The first call downloads the model if it is not cached.
    """
    return SentenceTransformer(MODEL_NAME)


def calculate_semantic_match(
    candidate_resume_text: str | None,
    job_description_text: str | None,
) -> dict:
    """
    Compare resume and job description using text embeddings.

    An unavailable calculation is represented by None rather than
    a misleading zero score.
    """

    if not candidate_resume_text or not candidate_resume_text.strip():
        return {
            "semantic_score": None,
            "semantic_available": False,
            "semantic_summary": "Candidate resume text is unavailable.",
        }

    if not job_description_text or not job_description_text.strip():
        return {
            "semantic_score": None,
            "semantic_available": False,
            "semantic_summary": "Job description text is unavailable.",
        }

    try:
        model = load_embedding_model()

        embeddings = model.encode(
            [
                candidate_resume_text.strip(),
                job_description_text.strip(),
            ],
            normalize_embeddings=True,
        )

        similarity = float(
            cosine_similarity(
                [embeddings[0]],
                [embeddings[1]],
            )[0][0]
        )

        if not math.isfinite(similarity):
            raise ValueError("Similarity calculation returned a non-finite value.")

        semantic_score = max(0.0, min(100.0, similarity * 100))

        return {
            "semantic_score": round(semantic_score, 2),
            "semantic_available": True,
            "semantic_summary": (
                "Semantic similarity between the candidate resume "
                "and the job description was calculated successfully."
            ),
        }

    except Exception:
        logger.exception("Semantic matching calculation failed.")

        return {
            "semantic_score": None,
            "semantic_available": False,
            "semantic_summary": (
                "Semantic matching is currently unavailable. "
                "This component was excluded from the overall score."
            ),
        }
