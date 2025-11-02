from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    user_id: str
    query: str
    context: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    context: Optional[str] = None

class DocumentChunk(BaseModel):
    chunk_id: str
    text: str
    metadata: dict

class RetrievalResponse(BaseModel):
    chunks: List[DocumentChunk]
    query: str
    user_id: str