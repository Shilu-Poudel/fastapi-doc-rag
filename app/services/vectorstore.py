import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.core.config import settings

# Supported similarity algorithms for the comparison study.
DISTANCES: dict[str, Distance] = {
    "cosine": Distance.COSINE,
    "dot": Distance.DOT,
    "euclid": Distance.EUCLID,
}


class QdrantStore:
    """Thin wrapper around a single Qdrant collection."""

    def __init__(
        self, collection: str | None = None, distance: str = "cosine"
    ) -> None:
        self.collection = collection or settings.qdrant_collection
        self.client = QdrantClient(
            url=settings.qdrant_url, api_key=settings.qdrant_api_key or None
        )
        self._ensure_collection(DISTANCES[distance])

    def _ensure_collection(self, distance: Distance) -> None:
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=settings.embedding_dim, distance=distance
                ),
            )

    def upsert(self, vector: list[float], payload: dict[str, Any]) -> str:
        point_id = str(uuid.uuid4())
        self.client.upsert(
            self.collection,
            points=[PointStruct(id=point_id, vector=vector, payload=payload)],
        )
        return point_id

    def search(self, vector: list[float], top_k: int = 5) -> list[dict[str, Any]]:
        result = self.client.query_points(
            self.collection, query=vector, limit=top_k, with_payload=True
        )
        return [
            {"id": point.id, "score": point.score, "payload": point.payload}
            for point in result.points
        ]
