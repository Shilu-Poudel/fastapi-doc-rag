from sqlalchemy import Column, Integer, String, Text
from app.db.base import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, index=True)
    chunk_text = Column(Text)
    metadata = Column(Text)  # You can use JSON or a string representation for metadata

    def __repr__(self):
        return f"<Document(id={self.id}, file_name={self.file_name})>"