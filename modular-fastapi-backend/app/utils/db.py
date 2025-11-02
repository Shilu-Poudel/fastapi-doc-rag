from typing import Generator
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class FileChunkMeta(Base):
    """Persistence model for file chunk metadata."""
    __tablename__ = "file_chunks"
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, index=True)
    chunk_id = Column(Integer, index=True)
    chunk_text = Column(Text)
    embedding_id = Column(String, index=True)

class Booking(Base):
    """Booking persistence model."""
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False)
    date = Column(String, nullable=False)
    time = Column(String, nullable=False)

def init_db() -> None:
    """Create DB tables if they do not exist."""
    Base.metadata.create_all(bind=engine)

def get_db_session() -> Session:
    """Return a SQLAlchemy session."""
    return SessionLocal()