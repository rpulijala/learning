"""Ingestion script for notes into ChromaDB vector store.

Usage:
    python -m backend.rag.ingest_notes
    
    # Use Ollama for embeddings (no OpenAI key needed):
    EMBEDDING_PROVIDER=ollama python -m backend.rag.ingest_notes
"""

from pathlib import Path

from backend.rag.embeddings import get_embeddings, get_embedding_provider
from backend.rag.store import get_chroma_client, get_notes_collection

# Notes directory
NOTES_DIR = Path(__file__).parent.parent / "notes"

# Chunk settings
CHUNK_SIZE = 500  # characters
CHUNK_OVERLAP = 50  # characters


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks.
    
    Args:
        text: The text to chunk.
        chunk_size: Maximum size of each chunk in characters.
        overlap: Number of overlapping characters between chunks.
        
    Returns:
        List of text chunks.
    """
    if len(text) <= chunk_size:
        return [text.strip()] if text.strip() else []
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        
        if chunk:
            chunks.append(chunk)
        
        start = end - overlap
        
        # Avoid infinite loop on very small texts
        if start >= len(text) - overlap:
            break
    
    return chunks




def scan_notes_directory() -> list[tuple[str, str]]:
    """Scan the notes directory for .md and .txt files.
    
    Returns:
        List of tuples (filename, content).
    """
    notes = []
    
    if not NOTES_DIR.exists():
        print(f"Notes directory not found: {NOTES_DIR}")
        return notes
    
    for file_path in NOTES_DIR.iterdir():
        if file_path.suffix.lower() in [".md", ".txt"]:
            try:
                content = file_path.read_text(encoding="utf-8")
                notes.append((file_path.name, content))
                print(f"  Found: {file_path.name} ({len(content)} chars)")
            except Exception as e:
                print(f"  Error reading {file_path.name}: {e}")
    
    return notes


def ingest_notes() -> None:
    """Main ingestion function - reads notes, chunks, embeds, and stores in ChromaDB."""
    print("=" * 50)
    print("Notes Ingestion Script")
    print("=" * 50)
    
    # Initialize clients
    print("\n[1/5] Initializing clients...")
    provider = get_embedding_provider()
    print(f"  Using embedding provider: {provider}")
    chroma_client = get_chroma_client()
    collection = get_notes_collection(chroma_client)
    
    # Clear existing data
    print("\n[2/5] Clearing existing collection...")
    existing_count = collection.count()
    if existing_count > 0:
        # Get all IDs and delete them
        all_ids = collection.get()["ids"]
        if all_ids:
            collection.delete(ids=all_ids)
        print(f"  Deleted {existing_count} existing documents")
    
    # Scan notes directory
    print(f"\n[3/5] Scanning notes directory: {NOTES_DIR}")
    notes = scan_notes_directory()
    
    if not notes:
        print("  No notes found!")
        return
    
    print(f"  Found {len(notes)} note file(s)")
    
    # Chunk all notes
    print("\n[4/5] Chunking notes...")
    all_chunks = []
    all_ids = []
    all_metadatas = []
    
    for filename, content in notes:
        chunks = chunk_text(content)
        print(f"  {filename}: {len(chunks)} chunk(s)")
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{filename}_{i}"
            all_chunks.append(chunk)
            all_ids.append(chunk_id)
            all_metadatas.append({
                "source": filename,
                "chunk_index": i,
            })
    
    if not all_chunks:
        print("  No chunks generated!")
        return
    
    print(f"  Total chunks: {len(all_chunks)}")
    
    # Generate embeddings
    print("\n[5/5] Generating embeddings and storing...")
    embeddings = get_embeddings(all_chunks)
    print(f"  Generated {len(embeddings)} embeddings")
    
    # Upsert into ChromaDB
    collection.upsert(
        ids=all_ids,
        documents=all_chunks,
        embeddings=embeddings,
        metadatas=all_metadatas,
    )
    
    print(f"  Stored {len(all_chunks)} chunks in ChromaDB")
    
    # Verify
    final_count = collection.count()
    print(f"\n✓ Ingestion complete! Collection now has {final_count} documents.")
    print("=" * 50)


if __name__ == "__main__":
    ingest_notes()
