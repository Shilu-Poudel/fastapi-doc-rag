"""Benchmark chunking strategies, embedding models and Qdrant distances.

Generates retrieval accuracy (hit@k) and latency numbers used in FINDINGS.md.
Run with the project venv while Qdrant is up:

    .venv/bin/python -m benchmarks.run_benchmark
"""

import time
import uuid

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.services.chunking import chunk_text

QDRANT = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key or None)
TOP_K = 3
SEARCH_DEPTH = 10  # how deep to look when computing MRR
CHUNK_SIZE = 250
CHUNK_OVERLAP = 40

EMBEDDING_MODELS = {
    "all-MiniLM-L6-v2": ("sentence-transformers/all-MiniLM-L6-v2", 384),
    "all-mpnet-base-v2": ("sentence-transformers/all-mpnet-base-v2", 768),
}
CHUNKING_STRATEGIES = ("recursive", "sentence", "fixed")
DISTANCES = {"cosine": Distance.COSINE, "dot": Distance.DOT, "euclid": Distance.EUCLID}

# Ground-truth set: question -> anchor keyword(s) unique to the correct fact.
# Questions are paraphrased (not lexically matching the source) and include
# confusable pairs (precision/recall, L1/L2, cosine/dot/euclid) so retrieval
# must discriminate, not just keyword-match.
QUESTIONS = [
    ("What share of my positive predictions were actually right?", ["precision measures the fraction of predicted positive"]),
    ("How many of the real positive cases did the model catch?", ["recall measures the fraction of real positive"]),
    ("What single score balances precision and recall?", ["f1 score is the harmonic mean"]),
    ("Which penalty zeroes out weights to create sparse models?", ["l1 regularization", "lasso"]),
    ("Which penalty shrinks weights smoothly without forcing zeros?", ["l2 regularization", "ridge"]),
    ("Why do the earliest layers of a deep net barely update?", ["vanishing gradient"]),
    ("What happens when gradients blow up and destabilize training?", ["exploding gradient"]),
    ("Which model slides filters over an image to find shapes?", ["convolutional neural network"]),
    ("Which network keeps memory across steps for text or audio?", ["recurrent neural network maintains"]),
    ("What added gates to RNNs to remember over long sequences?", ["long short-term memory"]),
    ("Which architecture dropped recurrence for attention in 2017?", ["transformer architecture replaced recurrence"]),
    ("What lets each token weigh the relevance of all others?", ["self-attention lets each token"]),
    ("What pits a generator against a discriminator?", ["generative adversarial"]),
    ("Which similarity ignores vector length and looks at angle?", ["cosine similarity measures the angle"]),
    ("Which distance is the straight-line gap between two points?", ["euclidean distance measures the straight-line"]),
    ("Which operation grows with vector magnitude?", ["dot product multiplies"]),
    ("Which learning style invents its own labels, like masked words?", ["self-supervised"]),
    ("Which method trains many models in parallel and averages them?", ["bagging trains many models"]),
    ("Which method trains models sequentially to fix prior errors?", ["boosting trains models sequentially"]),
    ("How do I reduce features by keeping directions of most variance?", ["principal component analysis"]),
    ("What groups data into k clusters around moving centroids?", ["k-means clustering"]),
    ("How can I reuse a big-dataset model for a new related task?", ["transfer learning"]),
    ("What trains an agent using rewards and penalties?", ["reinforcement learning trains an agent"]),
    ("Which optimizer uses one random example at a time?", ["stochastic gradient descent"]),
]

_model_cache: dict[str, SentenceTransformer] = {}


def _load_corpus() -> str:
    with open("benchmarks/corpus.txt", encoding="utf-8") as handle:
        return handle.read()


def _model(name: str) -> SentenceTransformer:
    if name not in _model_cache:
        _model_cache[name] = SentenceTransformer(name)
    return _model_cache[name]


def _embed(
    model: SentenceTransformer, texts: list[str], normalize: bool = True
) -> list[list[float]]:
    vectors = model.encode(texts, normalize_embeddings=normalize)
    return [vector.tolist() for vector in vectors]


def _recreate(collection: str, dim: int, distance: Distance) -> None:
    if QDRANT.collection_exists(collection):
        QDRANT.delete_collection(collection)
    QDRANT.create_collection(
        collection_name=collection,
        vectors_config=VectorParams(size=dim, distance=distance),
    )


def _index(
    collection: str,
    model: SentenceTransformer,
    chunks: list[str],
    normalize: bool = True,
) -> None:
    vectors = _embed(model, chunks, normalize)
    QDRANT.upsert(
        collection,
        points=[
            PointStruct(id=str(uuid.uuid4()), vector=vector, payload={"text": chunk})
            for vector, chunk in zip(vectors, chunks)
        ],
    )


def _rank_of_answer(points, keywords: list[str]) -> int | None:
    """1-based rank of the first retrieved chunk containing an anchor keyword."""
    for rank, point in enumerate(points, start=1):
        text = point.payload["text"].lower()
        if any(keyword in text for keyword in keywords):
            return rank
    return None


def _evaluate(
    collection: str, model: SentenceTransformer, normalize: bool = True
) -> dict[str, float]:
    """Return hit@1, hit@3, MRR and average embed/search latency in ms."""
    hit1 = hit3 = 0
    reciprocal_ranks: list[float] = []
    embed_ms: list[float] = []
    search_ms: list[float] = []
    for question, keywords in QUESTIONS:
        start = time.perf_counter()
        query_vector = _embed(model, [question], normalize)[0]
        embed_ms.append((time.perf_counter() - start) * 1000)

        start = time.perf_counter()
        result = QDRANT.query_points(collection, query=query_vector, limit=SEARCH_DEPTH)
        search_ms.append((time.perf_counter() - start) * 1000)

        rank = _rank_of_answer(result.points, keywords)
        reciprocal_ranks.append(1 / rank if rank else 0.0)
        if rank == 1:
            hit1 += 1
        if rank is not None and rank <= TOP_K:
            hit3 += 1

    n = len(QUESTIONS)
    return {
        "hit@1": hit1 / n,
        "hit@3": hit3 / n,
        "mrr": sum(reciprocal_ranks) / n,
        "embed_ms": sum(embed_ms) / n,
        "search_ms": sum(search_ms) / n,
    }


def report_chunking_and_embeddings(corpus: str) -> list[dict]:
    rows = []
    for model_label, (model_name, dim) in EMBEDDING_MODELS.items():
        model = _model(model_name)
        for strategy in CHUNKING_STRATEGIES:
            chunks = chunk_text(corpus, strategy=strategy, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
            collection = f"bench_{model_label}_{strategy}".replace("-", "_")
            _recreate(collection, dim, Distance.COSINE)
            _index(collection, model, chunks)
            metrics = _evaluate(collection, model)
            QDRANT.delete_collection(collection)
            rows.append(
                {
                    "embedding": model_label,
                    "chunking": strategy,
                    "chunks": len(chunks),
                    **metrics,
                }
            )
    return rows


def report_distances(corpus: str) -> list[dict]:
    """Compare distances on UN-normalized embeddings so magnitude matters."""
    model_name, dim = EMBEDDING_MODELS["all-MiniLM-L6-v2"]
    model = _model(model_name)
    chunks = chunk_text(corpus, strategy="recursive", chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
    rows = []
    for label, distance in DISTANCES.items():
        collection = f"bench_dist_{label}"
        _recreate(collection, dim, distance)
        _index(collection, model, chunks, normalize=False)
        metrics = _evaluate(collection, model, normalize=False)
        QDRANT.delete_collection(collection)
        rows.append({"distance": label, **metrics})
    return rows


def _print(title: str, rows: list[dict]) -> None:
    print(f"\n## {title}")
    headers = list(rows[0].keys())
    print(" | ".join(headers))
    for row in rows:
        print(
            " | ".join(
                f"{row[h]:.2f}" if isinstance(row[h], float) else str(row[h])
                for h in headers
            )
        )


if __name__ == "__main__":
    corpus = _load_corpus()
    _print("Chunking x Embedding (distance=cosine)", report_chunking_and_embeddings(corpus))
    _print("Similarity algorithm (MiniLM + recursive)", report_distances(corpus))
