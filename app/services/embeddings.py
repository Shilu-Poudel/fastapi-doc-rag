from functools import lru_cache

from sentence_transformers import SentenceTransformer

from app.core.config import settings


@lru_cache
def _model() -> SentenceTransformer:
    return SentenceTransformer(settings.embedding_model)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts with the configured local embedding model."""
    vectors = _model().encode(texts, normalize_embeddings=True)
    return [vector.tolist() for vector in vectors]


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]
