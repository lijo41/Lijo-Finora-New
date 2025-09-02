"""Search functionality agent with ADK tool structure."""

import logging
from typing import List, Dict, Any, Optional
from .document_agent import get_document_chunks

logger = logging.getLogger(__name__)

# ADK-style tool functions
def search_documents(query: str, limit: int = 10, document_id: Optional[str] = None) -> Dict[str, Any]:
    """Search through document chunks using text matching.
    
    Args:
        query: Search query string
        limit: Maximum number of results to return
        document_id: Optional specific document ID to search within
        
    Returns:
        Dict with status, results list, and count
    """
    try:
        # Get document chunks
        chunks_result = get_document_chunks(document_id)
        
        if chunks_result["status"] != "success":
            return {
                "status": "error",
                "error_message": "Failed to retrieve document chunks",
                "results": [],
                "count": 0
            }
        
        all_chunks = chunks_result["chunks"]
        
        if not all_chunks:
            return {
                "status": "success",
                "results": [],
                "count": 0,
                "message": "No documents available to search"
            }
        
        # Simple text search through chunks
        query_lower = query.lower()
        matching_chunks = []
        
        for chunk in all_chunks:
            chunk_text = chunk['text'].lower()
            
            # Calculate relevance score based on query matches
            relevance_score = 0
            query_words = query_lower.split()
            
            for word in query_words:
                if word in chunk_text:
                    relevance_score += chunk_text.count(word)
            
            if relevance_score > 0:
                matching_chunks.append({
                    "chunk_id": chunk['id'],
                    "document_id": chunk['document_id'],
                    "text": chunk['text'],
                    "relevance_score": relevance_score,
                    "metadata": chunk['metadata']
                })
        
        # Sort by relevance score (highest first)
        matching_chunks.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        # Limit results
        results = matching_chunks[:limit]
        
        return {
            "status": "success",
            "results": results,
            "count": len(results),
            "total_chunks_searched": len(all_chunks)
        }
        
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        return {
            "status": "error",
            "error_message": str(e),
            "results": [],
            "count": 0
        }

# Legacy wrapper class for backward compatibility
class SearchAgent:
    """Legacy wrapper for search operations - use ADK tool functions directly."""
    
    def __init__(self, document_agent=None):
        self.document_agent = document_agent
    
    async def search_documents(self, query: str, limit: int = 10, document_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Legacy method - use search_documents function directly."""
        result = search_documents(query, limit, document_id)
        return result.get("results", [])
