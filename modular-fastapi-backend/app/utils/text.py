# File: /modular-fastapi-backend/modular-fastapi-backend/app/utils/text.py

from typing import List

def chunk_text(text: str, chunk_size: int) -> List[str]:
    """Splits the input text into chunks of specified size."""
    return [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

def clean_text(text: str) -> str:
    """Cleans the input text by removing unnecessary whitespace and special characters."""
    return ' '.join(text.split())

def extract_keywords(text: str) -> List[str]:
    """Extracts keywords from the input text. Placeholder for a more complex implementation."""
    # This is a placeholder for a keyword extraction algorithm
    return text.split()[:5]  # Return first 5 words as keywords for simplicity

def summarize_text(text: str, max_length: int) -> str:
    """Summarizes the input text to a specified maximum length. Placeholder for a summarization algorithm."""
    return text[:max_length] + ('...' if len(text) > max_length else '')