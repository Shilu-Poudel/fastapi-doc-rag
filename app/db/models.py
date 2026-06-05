from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ChunkMetadata(Base):
    """Per-chunk metadata for an ingested document."""

    __tablename__ = "chunk_metadata"

    id: Mapped[int] = mapped_column(primary_key=True)
    file_name: Mapped[str] = mapped_column(String(255), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    chunking_strategy: Mapped[str] = mapped_column(String(32))
    embedding_model: Mapped[str] = mapped_column(String(64))
    vector_id: Mapped[str] = mapped_column(String(64), index=True)
    text: Mapped[str] = mapped_column(Text)


class Booking(Base):
    """Interview booking captured through the conversational agent."""

    __tablename__ = "bookings"

    id: Mapped[int] = mapped_column(primary_key=True)
    full_name: Mapped[str] = mapped_column(String(128))
    email: Mapped[str] = mapped_column(String(255), index=True)
    date: Mapped[str] = mapped_column(String(32))
    time: Mapped[str] = mapped_column(String(32))
