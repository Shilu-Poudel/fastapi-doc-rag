"""Legacy ingestion service placeholder; routers implement ingestion directly.
Simplify to avoid misleading imports.
"""

class IngestionService:
    def ingest_text(self, text: str) -> int:
        # Return count of chunks hypothetically processed; placeholder
        return max(1, len(text) // 500)