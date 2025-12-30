"""Embeddings module - supports OpenAI and Ollama embedding models."""

import os
from typing import Literal

import httpx
from openai import OpenAI

# Embedding provider type
EmbeddingProvider = Literal["openai", "ollama"]

# Default models
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
OLLAMA_EMBEDDING_MODEL = "nomic-embed-text"  # Run: ollama pull nomic-embed-text

# Ollama base URL
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


def get_embedding_provider() -> EmbeddingProvider:
    """Determine which embedding provider to use based on environment."""
    provider = os.getenv("EMBEDDING_PROVIDER", "openai").lower()
    if provider == "ollama":
        return "ollama"
    return "openai"


def get_embeddings_openai(texts: list[str]) -> list[list[float]]:
    """Get embeddings using OpenAI API."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    client = OpenAI(api_key=api_key)
    response = client.embeddings.create(
        model=OPENAI_EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]


def get_embeddings_ollama(texts: list[str]) -> list[list[float]]:
    """Get embeddings using Ollama API."""
    embeddings = []
    
    for text in texts:
        response = httpx.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={"model": OLLAMA_EMBEDDING_MODEL, "prompt": text},
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()
        embeddings.append(data["embedding"])
    
    return embeddings


def get_embeddings(texts: list[str], provider: EmbeddingProvider | None = None) -> list[list[float]]:
    """Get embeddings for a list of texts.
    
    Args:
        texts: List of texts to embed.
        provider: Embedding provider to use. If None, uses EMBEDDING_PROVIDER env var.
        
    Returns:
        List of embedding vectors.
    """
    if not texts:
        return []
    
    if provider is None:
        provider = get_embedding_provider()
    
    if provider == "ollama":
        return get_embeddings_ollama(texts)
    else:
        return get_embeddings_openai(texts)


def get_single_embedding(text: str, provider: EmbeddingProvider | None = None) -> list[float]:
    """Get embedding for a single text.
    
    Args:
        text: Text to embed.
        provider: Embedding provider to use.
        
    Returns:
        Embedding vector.
    """
    embeddings = get_embeddings([text], provider)
    return embeddings[0] if embeddings else []
