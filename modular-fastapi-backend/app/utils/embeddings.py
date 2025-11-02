from typing import List
import numpy as np

def generate_embeddings(texts: List[str], model) -> np.ndarray:
    """
    Generate embeddings for a list of texts using the specified model.

    Args:
        texts (List[str]): A list of texts to generate embeddings for.
        model: The model used for generating embeddings.

    Returns:
        np.ndarray: An array of embeddings corresponding to the input texts.
    """
    embeddings = model.encode(texts)
    return embeddings

def normalize_embeddings(embeddings: np.ndarray) -> np.ndarray:
    """
    Normalize the embeddings to unit length.

    Args:
        embeddings (np.ndarray): The embeddings to normalize.

    Returns:
        np.ndarray: The normalized embeddings.
    """
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized_embeddings = embeddings / norms
    return normalized_embeddings