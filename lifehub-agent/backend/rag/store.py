"""ChromaDB vector store setup for notes collection."""

from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings

# Persistent storage directory for ChromaDB
CHROMA_PERSIST_DIR = Path(__file__).parent.parent / "state" / "chroma"


def get_chroma_client() -> Any:
    """Get or create a persistent ChromaDB client.
    
    Returns:
        A ChromaDB PersistentClient instance.
    """
    CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(CHROMA_PERSIST_DIR),
        settings=Settings(anonymized_telemetry=False),
    )


def get_notes_collection(client: Any = None):
    """Get or create the 'notes' collection in ChromaDB.
    
    Args:
        client: Optional ChromaDB client. If not provided, creates a new one.
        
    Returns:
        The 'notes' collection.
    """
    if client is None:
        client = get_chroma_client()
    
    return client.get_or_create_collection(
        name="notes",
        metadata={"description": "Personal notes and documents"},
    )
