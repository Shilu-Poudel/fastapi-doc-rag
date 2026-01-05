"""Legacy placeholder RAG service; not used by routers.
Keeping for future expansion but removing broken imports.
"""

from typing import List

class RAGService:
    def process_query(self, query_text: str) -> str:
        # Placeholder simple echo; real logic is handled in chat router via EmbeddingService + VectorStore + Groq
        return f"You asked: {query_text}"