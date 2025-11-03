from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from app.schemas.document import DocumentCreate
from app.services.ingestion_service import IngestionService

router = APIRouter()
ingestion_service = IngestionService()

@router.post("/ingest", response_model=DocumentCreate)
async def ingest_document(file: UploadFile = File(...)):
    try:
        document = await ingestion_service.process_file(file)
        return document
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))