from pydantic import BaseModel
from typing import List, Optional

class DocumentBase(BaseModel):
    file_name: str
    chunk_text: str
    metadata: Optional[dict] = None

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase):
    id: int

    class Config:
        orm_mode = True

class DocumentList(BaseModel):
    documents: List[Document]