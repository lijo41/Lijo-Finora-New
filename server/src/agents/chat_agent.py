"""Chat functionality agent with ADK tool structure."""

import logging
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv
from .document_agent import get_document_chunks

# AI API imports
try:
    import google.generativeai as genai
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

load_dotenv()
logger = logging.getLogger(__name__)

# Initialize AI clients globally
_google_client = None
_groq_client = None

def _initialize_ai_clients():
    """Initialize AI clients if not already done."""
    global _google_client, _groq_client
    
    if _google_client is None and GOOGLE_AVAILABLE and os.getenv("GOOGLE_API_KEY"):
        try:
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            _google_client = genai.GenerativeModel('gemini-pro')
            logger.info("Google Gemini client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Google client: {e}")
    
    if _groq_client is None and GROQ_AVAILABLE and os.getenv("GROQ_API_KEY"):
        try:
            _groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            logger.info("Groq client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Groq client: {e}")

# ADK-style tool functions
def chat_with_documents(query: str, document_id: Optional[str] = None, context_limit: int = 5) -> Dict[str, Any]:
    """Chat with documents using ordered chunks for context-aware responses.
    
    Args:
        query: User's chat query
        document_id: Optional specific document ID to chat with
        context_limit: Maximum number of chunks to use for context
        
    Returns:
        Dict with status, response, context_chunks count, and sources
    """
    try:
        # Initialize AI clients
        _initialize_ai_clients()
        
        # Get all document chunks in order
        chunks_result = get_document_chunks(document_id)
        
        if chunks_result["status"] != "success":
            return {
                "status": "error",
                "error_message": "Failed to retrieve document chunks",
                "response": "Sorry, I couldn't access the documents.",
                "context_chunks": 0,
                "sources": []
            }
        
        all_chunks = chunks_result["chunks"]
        
        if not all_chunks:
            # No documents available - provide general AI response
            ai_response = _generate_ai_response(query, "")
            return {
                "status": "success",
                "response": ai_response,
                "context_chunks": 0,
                "sources": []
            }
        
        # Use all chunks in order for comprehensive context
        context_chunks = all_chunks[:context_limit * 2]  # Get more chunks for better context
        
        # Build structured context from ordered chunks
        context_sections = []
        current_doc = None
        current_content = []
        
        for chunk in context_chunks:
            doc_name = chunk['metadata'].get('file_name', 'Unknown')
            
            # Group chunks by document
            if current_doc != doc_name:
                if current_doc and current_content:
                    context_sections.append(f"=== {current_doc} ===\n" + "\n".join(current_content))
                current_doc = doc_name
                current_content = []
            
            current_content.append(chunk['text'])
        
        # Add final document
        if current_doc and current_content:
            context_sections.append(f"=== {current_doc} ===\n" + "\n".join(current_content))
        
        context = "\n\n".join(context_sections)
        
        # Generate AI response with full context
        ai_response = _generate_ai_response(query, context)
        
        # Get unique source documents
        sources = list(set([chunk['metadata'].get('file_name', 'Unknown') for chunk in context_chunks]))
        
        return {
            "status": "success",
            "response": ai_response,
            "context_chunks": len(context_chunks),
            "sources": sources
        }
        
    except Exception as e:
        logger.error(f"Error in chat with documents: {str(e)}")
        return {
            "status": "error",
            "error_message": str(e),
            "response": "Sorry, I encountered an error while processing your request.",
            "context_chunks": 0,
            "sources": []
        }

def _generate_ai_response(query: str, context: str) -> str:
    """Generate AI response using available AI services."""
    prompt = _build_prompt(query, context)
    
    # Try Google Gemini first
    if _google_client:
        try:
            response = _google_client.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.warning(f"Google Gemini failed: {e}")
    
    # Fallback to Groq
    if _groq_client:
        try:
            response = _groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.warning(f"Groq failed: {e}")
    
    # Fallback response
    return "I'm sorry, but I'm currently unable to process your request due to AI service limitations. Please check your API configurations."

def _build_prompt(query: str, context: str) -> str:
    """Build prompt for AI response generation."""
    if context:
        return f"""You are a helpful assistant that answers questions based on document content.

Context from documents:
{context}

User question: {query}

Please provide a helpful and accurate answer based on the context provided. If the context doesn't contain relevant information, please say so clearly."""
    else:
        return f"""You are a helpful assistant. Please answer the following question:

{query}

Note: No specific document context is available for this query."""

# Legacy wrapper class for backward compatibility
class ChatAgent:
    """Legacy wrapper for chat operations - use ADK tool functions directly."""
    
    def __init__(self, document_agent=None):
        self.document_agent = document_agent
        # Initialize AI clients
        _initialize_ai_clients()
        self.google_client = _google_client
        self.groq_client = _groq_client
    
    async def chat_with_documents(self, query: str, document_id: Optional[str] = None, context_limit: int = 5) -> Dict[str, Any]:
        """Legacy method - use chat_with_documents function directly."""
        return chat_with_documents(query, document_id, context_limit)
