from typing import List
import re

def chunk_text_fixed(text: str, chunk_size: int = 500) -> List[str]:
    """
    Naive fixed-size chunking by whitespace tokens (approximate tokens).
    Splits text into chunks of chunk_size tokens.
    """
    tokens = text.split()
    chunks = []
    for i in range(0, len(tokens), chunk_size):
        chunk = " ".join(tokens[i : i + chunk_size])
        chunks.append(chunk)
    return chunks

def chunk_text_sentences(text: str, chunk_size: int = 500) -> List[str]:
    """
    Sentence-split chunking: group sentences until approximate chunk_size tokens reached.
    """
    # very simple sentence splitter
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = []
    current_count = 0
    for s in sentences:
        toks = s.split()
        if current_count + len(toks) > chunk_size and current:
            chunks.append(" ".join(current))
            current = [s]
            current_count = len(toks)
        else:
            current.append(s)
            current_count += len(toks)
    if current:
        chunks.append(" ".join(current))
    return chunks