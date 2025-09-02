"""Document parsing and chunking agent using Docling with ADK tool structure."""

import os
import tempfile
from typing import List, Dict, Any, Optional
from pathlib import Path
from docling.document_converter import DocumentConverter
import uuid
import logging

logger = logging.getLogger(__name__)

# Global storage (in production, use proper database)
_document_storage: Dict[str, Any] = {}
_chunk_storage: Dict[str, Any] = {}

# ADK-style tool functions
def upload_document(file_content: bytes, filename: str) -> Dict[str, Any]:
    """Upload and process a document file.
    
    Args:
        file_content: The binary content of the file
        filename: Name of the file being uploaded
        
    Returns:
        Dict with status, document_id, chunks_count, and metadata
    """
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(filename).suffix) as temp_file:
            temp_file.write(file_content)
            temp_path = temp_file.name
        
        # Parse document
        converter = DocumentConverter()
        result = converter.convert(temp_path)
        content = result.document.export_to_markdown()
        
        # Clean up temp file
        os.unlink(temp_path)
        
        # Create metadata
        metadata = {
            "file_name": filename,
            "pages": len(result.document.pages) if hasattr(result.document, 'pages') else 1,
            "format": Path(filename).suffix.lower(),
            "created_at": str(uuid.uuid4())
        }
        
        # Chunk document
        chunks = chunk_document_content(content)
        document_id = store_document_chunks(chunks, metadata)
        
        return {
            "status": "success",
            "document_id": document_id,
            "chunks_count": len(chunks),
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"Error uploading document {filename}: {str(e)}")
        return {
            "status": "error",
            "error_message": str(e)
        }

def upload_document_url(url: str) -> Dict[str, Any]:
    """Upload and process a document from URL.
    
    Args:
        url: URL of the document to process
        
    Returns:
        Dict with status, document_id, chunks_count, and metadata
    """
    try:
        converter = DocumentConverter()
        result = converter.convert(url)
        content = result.document.export_to_markdown()
        
        metadata = {
            "url": url,
            "file_name": url.split("/")[-1],
            "format": "url",
            "created_at": str(uuid.uuid4())
        }
        
        chunks = chunk_document_content(content)
        document_id = store_document_chunks(chunks, metadata)
        
        return {
            "status": "success",
            "document_id": document_id,
            "chunks_count": len(chunks),
            "metadata": metadata
        }
        
    except Exception as e:
        logger.error(f"Error uploading document from URL {url}: {str(e)}")
        return {
            "status": "error",
            "error_message": str(e)
        }

def get_document_chunks(document_id: Optional[str] = None) -> Dict[str, Any]:
    """Get document chunks for processing.
    
    Args:
        document_id: Optional specific document ID to filter chunks
        
    Returns:
        Dict with status, chunks list, and count
    """
    try:
        if document_id and document_id in _document_storage:
            # Get chunks for specific document
            chunks = [chunk for chunk in _chunk_storage.values() 
                     if chunk['document_id'] == document_id]
        else:
            # Get all chunks
            chunks = list(_chunk_storage.values())
        
        return {
            "status": "success",
            "chunks": chunks,
            "count": len(chunks)
        }
        
    except Exception as e:
        logger.error(f"Error getting document chunks: {str(e)}")
        return {
            "status": "error",
            "error_message": str(e),
            "chunks": [],
            "count": 0
        }

def clear_database() -> Dict[str, Any]:
    """Clear all stored documents and chunks.
    
    Returns:
        Dict with status and message
    """
    try:
        global _document_storage, _chunk_storage
        _document_storage.clear()
        _chunk_storage.clear()
        
        return {
            "status": "success",
            "message": "Database cleared successfully"
        }
        
    except Exception as e:
        logger.error(f"Error clearing database: {str(e)}")
        return {
            "status": "error",
            "error_message": str(e)
        }

def get_server_status() -> Dict[str, Any]:
    """Get server status including document and chunk counts.
    
    Returns:
        Dict with status information
    """
    try:
        return {
            "status": "success",
            "documents_count": len(_document_storage),
            "chunks_count": len(_chunk_storage),
            "agents": {
                "document_agent": "active",
                "search_agent": "active",
                "chat_agent": "active",
                "gstr1_agent": "active"
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting server status: {str(e)}")
        return {
            "status": "error",
            "error_message": str(e)
        }

# Helper functions
def chunk_document_content(content: str, chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
    """Chunk document content into smaller pieces."""
    chunks = []
    start = 0
    chunk_id = 0
    
    while start < len(content):
        end = min(start + chunk_size, len(content))
        
        # Try to break at sentence boundary
        if end < len(content):
            last_period = content.rfind('.', start, end)
            if last_period > start + chunk_size // 2:
                end = last_period + 1
        
        chunk_text = content[start:end].strip()
        
        if chunk_text:
            chunks.append({
                "id": str(uuid.uuid4()),
                "chunk_id": chunk_id,
                "text": chunk_text,
                "start_pos": start,
                "end_pos": end,
                "length": len(chunk_text)
            })
            chunk_id += 1
        
        start = max(start + chunk_size - overlap, end)
    
    return chunks

def store_document_chunks(chunks: List[Dict[str, Any]], metadata: Dict[str, Any]) -> str:
    """Store document chunks in memory."""
    document_id = str(uuid.uuid4())
    
    # Store document metadata
    _document_storage[document_id] = {
        "id": document_id,
        "metadata": metadata,
        "chunks_count": len(chunks),
        "created_at": metadata.get("created_at", "")
    }
    
    # Store chunks with document reference
    for chunk in chunks:
        chunk_full_id = f"{document_id}_{chunk['chunk_id']}"
        _chunk_storage[chunk_full_id] = {
            "id": chunk_full_id,
            "document_id": document_id,
            "chunk_id": chunk['chunk_id'],
            "text": chunk['text'],
            "metadata": {**metadata, **chunk}
        }
    
    logger.info(f"Stored {len(chunks)} chunks for document {document_id}")
    return document_id

def get_all_documents() -> Dict[str, Any]:
    """Get all stored documents.
    
    Returns:
        Dict with status, documents list, and count
    """
    try:
        documents = list(_document_storage.values())
        return {
            "status": "success",
            "documents": documents,
            "count": len(documents)
        }
    except Exception as e:
        logger.error(f"Error getting all documents: {str(e)}")
        return {
            "status": "error",
            "error_message": str(e),
            "documents": [],
            "count": 0
        }

# Legacy wrapper class for backward compatibility
class DocumentAgent:
    """Legacy wrapper for document operations - use ADK tool functions directly."""
    
    def __init__(self, storage_dir: str = "./documents_storage"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
    
    async def process_uploaded_file(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Legacy method - use upload_document function directly."""
        result = upload_document(file_content, filename)
        return {"success": result["status"] == "success", **result}
    
    async def get_document_chunks(self, document_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Legacy method - use get_document_chunks function directly."""
        result = get_document_chunks(document_id)
        return result.get("chunks", [])
    
    def get_all_documents(self) -> List[Dict[str, Any]]:
        """Get all stored documents."""
        return list(_document_storage.values())
    
    def clear_all_data(self) -> Dict[str, Any]:
        """Legacy method - use clear_database function directly."""
        result = clear_database()
        return {"success": result["status"] == "success", **result}
