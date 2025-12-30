"""Notes search tool - searches personal notes using RAG."""

from langchain_core.tools import tool

from backend.rag.embeddings import get_single_embedding
from backend.rag.store import get_notes_collection


@tool
def search_notes(query: str, top_k: int = 5) -> list[dict]:
    """Search personal notes for relevant information.
    
    Use this tool when the user asks about their notes, personal information,
    or when they want to find something they've written down before.
    
    Args:
        query: The search query to find relevant notes.
        top_k: Number of results to return (default 5).
        
    Returns:
        A list of relevant note chunks with content, source filename, and relevance score.
    """
    try:
        # Get the notes collection
        collection = get_notes_collection()
        
        # Check if collection has any documents
        if collection.count() == 0:
            return [{
                "content": "No notes have been indexed yet. Please run the ingestion script first.",
                "source": "system",
                "score": 0.0,
            }]
        
        # Get query embedding
        query_embedding = get_single_embedding(query)
        
        # Search the collection
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, collection.count()),
            include=["documents", "metadatas", "distances"],
        )
        
        # Format results
        formatted_results = []
        
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                distance = results["distances"][0][i] if results["distances"] else 0.0
                
                # Convert distance to similarity score (ChromaDB uses L2 distance by default)
                # Lower distance = more similar, so we invert it
                score = 1.0 / (1.0 + distance)
                
                formatted_results.append({
                    "content": doc,
                    "source": metadata.get("source", "unknown"),
                    "score": round(score, 4),
                })
        
        if not formatted_results:
            return [{
                "content": "No relevant notes found for your query.",
                "source": "system",
                "score": 0.0,
            }]
        
        return formatted_results
        
    except Exception as e:
        return [{
            "content": f"Error searching notes: {str(e)}",
            "source": "error",
            "score": 0.0,
        }]
