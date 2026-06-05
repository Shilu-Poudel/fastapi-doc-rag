from pydantic import BaseModel


class IngestionResult(BaseModel):
    """Summary returned after a document is ingested."""

    file_name: str
    chunking_strategy: str
    embedding_model: str
    chunks_ingested: int
