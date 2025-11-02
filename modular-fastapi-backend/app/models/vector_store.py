from sqlalchemy import Column, String, Float, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class VectorStore(Base):
    __tablename__ = 'vector_store'

    id = Column(Integer, primary_key=True, index=True)
    vector = Column(Float, nullable=False)  # Assuming vector is stored as a float array
    metadata = Column(String, nullable=True)  # Additional metadata associated with the vector

    def __repr__(self):
        return f"<VectorStore(id={self.id}, vector={self.vector}, metadata={self.metadata})>"