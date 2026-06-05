import re

from langchain_text_splitters import RecursiveCharacterTextSplitter

CHUNKING_STRATEGIES = ("recursive", "sentence", "fixed")


def _recursive(text: str, chunk_size: int, overlap: int) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=overlap
    )
    return splitter.split_text(text)


def _sentence(text: str, chunk_size: int) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks: list[str] = []
    buffer = ""
    for sentence in sentences:
        if buffer and len(buffer) + len(sentence) > chunk_size:
            chunks.append(buffer.strip())
            buffer = sentence
        else:
            buffer = f"{buffer} {sentence}".strip()
    if buffer:
        chunks.append(buffer.strip())
    return chunks


def _fixed(text: str, chunk_size: int) -> list[str]:
    return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]


def chunk_text(
    text: str, strategy: str = "recursive", chunk_size: int = 800, overlap: int = 100
) -> list[str]:
    """Split text into chunks using the requested strategy."""
    if strategy == "recursive":
        chunks = _recursive(text, chunk_size, overlap)
    elif strategy == "sentence":
        chunks = _sentence(text, chunk_size)
    elif strategy == "fixed":
        chunks = _fixed(text, chunk_size)
    else:
        raise ValueError(f"Unknown chunking strategy: {strategy}")
    return [chunk for chunk in chunks if chunk.strip()]
