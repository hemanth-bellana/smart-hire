from functools import lru_cache

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


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
    Compare a candidate's resume with a job description
    using text embeddings and cosine similarity.
    """

    if not candidate_resume_text or not candidate_resume_text.strip():
        return {
            "semantic_score": 0.0,
            "semantic_summary": "Candidate resume text is unavailable.",
        }

    if not job_description_text or not job_description_text.strip():
        return {
            "semantic_score": 0.0,
            "semantic_summary": "Job description text is unavailable.",
        }

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

    # Cosine similarity can be negative.
    # Keep the displayed score within 0–100.
    semantic_score = max(0.0, min(100.0, similarity * 100))

    return {
        "semantic_score": round(semantic_score, 2),
        "semantic_summary": (
            "Semantic similarity between the candidate resume "
            "and the job description was calculated successfully."
        ),
    }
