"""Orchestrator agent to coordinate all other agents."""

import logging
import os
from typing import Dict, Any, List, Optional
from .document_agent import upload_document, get_document_chunks, clear_database, get_all_documents
from .search_agent import search_documents
from .chat_agent import chat_with_documents
from .gstr1_agent import get_gstr1_chunks, process_gstr1_chunks, generate_gstr1_summary

logger = logging.getLogger(__name__)


class OrchestratorAgent:
    """Main orchestrator that coordinates all specialized agents using ADK tool functions."""
    
    def __init__(self, storage_dir: str = "./documents_storage"):
        self.storage_dir = storage_dir
        logger.info("Orchestrator initialized with ADK tool functions")
    
    async def process_task(self, task_type: str, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a task by routing to appropriate agent."""
        try:
            if task_type == "document_upload":
                return await self._handle_document_upload(task_data)
            elif task_type == "document_url":
                return await self._handle_document_url(task_data)
            elif task_type == "search":
                return await self._handle_search(task_data)
            elif task_type == "chat":
                return await self._handle_chat(task_data)
            elif task_type == "gstr1_chunks":
                return await self._handle_gstr1_chunks(task_data)
            elif task_type == "gstr1_process":
                return await self._handle_gstr1_process(task_data)
            elif task_type == "gstr1_summary":
                return await self._handle_gstr1_summary(task_data)
            else:
                return {
                    "success": False,
                    "error": f"Unknown task type: {task_type}"
                }
                
        except Exception as e:
            logger.error(f"Error processing task {task_type}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _handle_document_upload(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle document upload task."""
        file_content = task_data.get("file_content")
        filename = task_data.get("filename")
        
        if not file_content or not filename:
            return {
                "success": False,
                "error": "Missing file_content or filename"
            }
        
        return upload_document(file_content, filename)
    
    async def _handle_document_url(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle document URL parsing task."""
        url = task_data.get("url")
        
        if not url:
            return {
                "success": False,
                "error": "Missing URL"
            }
        
        # URL parsing not implemented in ADK tools yet
        return {
            "success": False,
            "error": "URL parsing not implemented in ADK tools"
        }
    
    async def _handle_search(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle search task."""
        query = task_data.get("query")
        limit = task_data.get("limit", 10)
        document_id = task_data.get("document_id")
        
        if not query:
            return {
                "success": False,
                "error": "Missing search query"
            }
        
        result = search_documents(query, limit, document_id)
        
        return {
            "success": result["status"] == "success",
            "results": result["results"],
            "count": result["count"],
            "error": result.get("error_message")
        }
    
    async def _handle_chat(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle chat task."""
        query = task_data.get("query")
        document_id = task_data.get("document_id")
        context_limit = task_data.get("context_limit", 5)
        
        if not query:
            return {
                "success": False,
                "error": "Missing chat query"
            }
        
        result = chat_with_documents(query, document_id, context_limit)
        
        return {
            "success": result["status"] == "success",
            "response": result["response"],
            "context_chunks": result["context_chunks"],
            "sources": result["sources"],
            "error": result.get("error_message")
        }
    
    async def _handle_gstr1_chunks(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GSTR-1 chunks retrieval task."""
        document_id = task_data.get("document_id")
        result = get_gstr1_chunks(document_id)
        
        return {
            "success": result["status"] == "success",
            "chunks": result["chunks"],
            "count": result["count"],
            "error": result.get("error_message")
        }
    
    async def _handle_gstr1_process(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GSTR-1 chunk processing task."""
        chunk_ids = task_data.get("chunk_ids", [])
        
        if not chunk_ids:
            return {
                "success": False,
                "error": "Missing chunk_ids"
            }
        
        result = process_gstr1_chunks(chunk_ids)
        
        return {
            "success": result["status"] == "success",
            "processed_chunks": result["processed_chunks"],
            "count": result["count"],
            "error": result.get("error_message")
        }
    
    async def _handle_gstr1_summary(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle GSTR-1 summary generation task."""
        processed_chunks = task_data.get("processed_chunks", [])
        user_header = task_data.get("user_header")
        
        if not processed_chunks:
            return {
                "success": False,
                "error": "Missing processed_chunks"
            }
        
        result = generate_gstr1_summary(processed_chunks, user_header)
        
        return {
            "success": result["status"] == "success",
            "gstr1_return": result["gstr1_return"],
            "sources_processed": result["sources_processed"],
            "chunks_processed": result.get("chunks_processed", []),
            "generated_at": result.get("generated_at"),
            "error": result.get("error_message")
        }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get status of all agents and system."""
        try:
            # Get document count using ADK functions
            all_documents = get_all_documents()
            chunks_result = get_document_chunks()
            
            chunks_count = chunks_result["count"] if chunks_result["status"] == "success" else 0
            
            # Check AI service availability
            google_available = bool(os.getenv("GOOGLE_API_KEY"))
            groq_available = bool(os.getenv("GROQ_API_KEY"))
            
            return {
                "success": True,
                "status": "running",
                "agents": {
                    "document_agent": "active",
                    "search_agent": "active", 
                    "chat_agent": "active",
                    "gstr1_agent": "active"
                },
                "documents_count": len(all_documents["documents"]) if all_documents["status"] == "success" else 0,
                "chunks_count": chunks_count,
                "ai_services": {
                    "google_gemini": "available" if google_available else "unavailable",
                    "groq": "available" if groq_available else "unavailable"
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def clear_database(self) -> Dict[str, Any]:
        """Clear all stored documents and chunks."""
        try:
            result = clear_database()
            return {
                "success": result["status"] == "success",
                "message": result.get("message", "Database cleared"),
                "error": result.get("error_message")
            }
            
        except Exception as e:
            logger.error(f"Error clearing database: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
