from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models.document import Document
from app.utils.text import extract_text, chunk_text
from app.utils.embeddings import generate_embeddings

class IngestionService:
    def __init__(self, db: Session):
        self.db = db

    def ingest_document(self, file: Any, metadata: Dict[str, Any]) -> List[Document]:
        text = extract_text(file)
        chunks = chunk_text(text)
        embeddings = generate_embeddings(chunks)

        documents = []
        for chunk, embedding in zip(chunks, embeddings):
            document = Document(
                file_name=metadata.get("file_name"),
                chunk_text=chunk,
                embedding=embedding,
                metadata=metadata
            )
            self.db.add(document)
            documents.append(document)

        self.db.commit()
        return documents

    def get_documents(self) -> List[Document]:
        return self.db.query(Document).all()