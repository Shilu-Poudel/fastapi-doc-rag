from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import ChunkMetadata
from app.db.session import get_db
from app.schemas.document import IngestionResult
from app.services.chunking import CHUNKING_STRATEGIES, chunk_text
from app.services.embeddings import embed_texts
from app.services.text_extractor import SUPPORTED_CONTENT_TYPES, extract_text
from app.services.vectorstore import QdrantStore

router = APIRouter()


@router.post("", response_model=IngestionResult)
async def ingest_document(
    file: UploadFile = File(...),
    chunking_strategy: str = Query("recursive", enum=list(CHUNKING_STRATEGIES)),
    db: Session = Depends(get_db),
) -> IngestionResult:
    """Extract, chunk, embed and store an uploaded PDF/TXT document."""
    if file.content_type not in SUPPORTED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    if file.size is not None and file.size > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds the {settings.max_upload_bytes} byte limit",
        )

    text = await extract_text(file)
    if not text.strip():
        raise HTTPException(status_code=400, detail="File contains no extractable text")

    chunks = chunk_text(text, strategy=chunking_strategy)
    if len(chunks) > settings.max_chunks:
        raise HTTPException(
            status_code=413,
            detail=f"Document too large: {len(chunks)} chunks exceeds the "
            f"{settings.max_chunks} chunk limit",
        )
    vectors = embed_texts(chunks)
    store = QdrantStore()

    for index, (chunk, vector) in enumerate(zip(chunks, vectors)):
        vector_id = store.upsert(
            vector,
            {"text": chunk, "file_name": file.filename, "chunk_index": index},
        )
        db.add(
            ChunkMetadata(
                file_name=file.filename or "unknown",
                chunk_index=index,
                chunking_strategy=chunking_strategy,
                embedding_model=settings.embedding_model,
                vector_id=vector_id,
                text=chunk,
            )
        )
    db.commit()

    return IngestionResult(
        file_name=file.filename or "unknown",
        chunking_strategy=chunking_strategy,
        embedding_model=settings.embedding_model,
        chunks_ingested=len(chunks),
    )
