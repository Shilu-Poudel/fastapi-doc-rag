from typing import Any, Dict, List
import os
import uuid

USE_QDRANT = os.getenv("USE_QDRANT", "false").lower() in ("1", "true", "yes")
QDRANT_URL = os.getenv("QDRANT_URL", "")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "documents")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))

class SimpleVectorStore:
    """In-memory vector store for local development / tests."""
    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, Any]] = {}

    def upsert_vector(self, vector: List[float], payload: Dict[str, Any]) -> str:
        vec_id = str(uuid.uuid4())
        self._store[vec_id] = {"vector": vector, "payload": payload}
        return vec_id

    def search_vector(self, vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        # Very simple placeholder ranking: return last inserted items
        out = []
        items = list(self._store.items())[-top_k:]
        for vid, data in items:
            out.append({"id": vid, "score": 1.0, "payload": data["payload"]})
        return out

class QdrantVectorStore:
    """Qdrant-backed vector store. Loads qdrant-client at runtime."""
    def __init__(self) -> None:
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.http import models as rest
        except ModuleNotFoundError as exc:
            raise RuntimeError("qdrant-client is not installed. Run: pip install qdrant-client") from exc

        if not QDRANT_URL:
            raise RuntimeError("QDRANT_URL not set in environment")

        self.client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)

        # Ensure collection exists (recreate if missing)
        try:
            self.client.get_collection(collection_name=QDRANT_COLLECTION)
        except Exception:
            self.client.recreate_collection(
                collection_name=QDRANT_COLLECTION,
                vectors_config=rest.VectorParams(size=EMBEDDING_DIM, distance=rest.Distance.COSINE),
            )

    def upsert_vector(self, vector: List[float], payload: Dict[str, Any]) -> str:
        from qdrant_client.http import models as rest
        vec_id = str(uuid.uuid4())
        self.client.upsert(
            collection_name=QDRANT_COLLECTION,
            points=[rest.PointStruct(id=vec_id, vector=vector, payload=payload)],
        )
        return vec_id

    def search_vector(self, vector: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        results = self.client.search(collection_name=QDRANT_COLLECTION, query_vector=vector, limit=top_k)
        out = []
        for r in results:
            out.append({"id": r.id, "score": r.score, "payload": r.payload})
        return out

# Export VectorStore class according to env
VectorStore = QdrantVectorStore if USE_QDRANT else SimpleVectorStore