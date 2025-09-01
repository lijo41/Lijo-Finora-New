"""GSTR-1 filing routes."""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.gstr1_processor import GSTR1Processor
from usecases.document_usecase import DocumentUseCase
from middleware.auth import get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gstr1", tags=["gstr1"])

class ChunkSelectionRequest(BaseModel):
    chunk_ids: List[str]

class CompanyDetails(BaseModel):
    gstin: str
    legal_name: str
    trade_name: str = ""
    return_period: str

class GSTR1ProcessRequest(BaseModel):
    chunk_ids: List[str]
    company_details: CompanyDetails

@router.get("/chunks")
async def get_available_chunks(current_user: dict = Depends(get_current_user_optional)):
    """Get all available document chunks for GSTR-1 processing."""
    try:
        document_usecase = DocumentUseCase()
        chunks = await document_usecase.get_all_chunks()
        
        return {
            "success": True,
            "chunks": [
                {
                    "id": chunk["id"],
                    "content": chunk["content"][:500] + "..." if len(chunk["content"]) > 500 else chunk["content"],
                    "document_name": chunk.get("document_name", "Unknown"),
                    "chunk_index": chunk.get("chunk_index", 0)
                }
                for chunk in chunks
            ]
        }
    except Exception as e:
        logger.error(f"Error getting chunks: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve chunks")

@router.post("/process")
async def process_gstr1_data(
    request: GSTR1ProcessRequest,
    current_user: dict = Depends(get_current_user_optional)
):
    """Process selected chunks to extract GSTR-1 data."""
    try:
        if not request.chunk_ids:
            raise HTTPException(status_code=400, detail="No chunks selected")
        
        document_usecase = DocumentUseCase()
        gstr1_processor = GSTR1Processor()
        
        # Get chunk contents
        chunk_contents = []
        for chunk_id in request.chunk_ids:
            chunk = await document_usecase.get_chunk_by_id(chunk_id)
            if chunk:
                chunk_contents.append(chunk["content"])
        
        if not chunk_contents:
            raise HTTPException(status_code=404, detail="No valid chunks found")
        
        # Process chunks for GSTR-1 data
        gstr1_data = await gstr1_processor.process_chunks_for_gstr1(chunk_contents)
        
        return {
            "success": True,
            "gstr1_data": gstr1_data,
            "processed_chunks": len(chunk_contents)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing GSTR-1 data: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process GSTR-1 data")

@router.post("/process-chunk")
async def process_single_chunk(
    chunk_id: str,
    current_user: dict = Depends(get_current_user_optional)
):
    """Process a single chunk to extract GSTR-1 data."""
    try:
        document_usecase = DocumentUseCase()
        gstr1_processor = GSTR1Processor()
        
        # Get chunk content
        chunk = await document_usecase.get_chunk_by_id(chunk_id)
        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk not found")
        
        # Process chunk for GSTR-1 data
        gstr1_data = await gstr1_processor.process_chunk_for_gstr1(chunk["content"])
        
        return {
            "success": True,
            "gstr1_data": gstr1_data,
            "chunk_id": chunk_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing chunk for GSTR-1: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process chunk")

@router.post("/generate-summary")
async def generate_gstr1_summary(
    request: GSTR1ProcessRequest,
    current_user: dict = Depends(get_current_user_optional)
):
    """Generate a comprehensive GSTR-1 summary from selected chunks."""
    try:
        if not request.chunk_ids:
            raise HTTPException(status_code=400, detail="No chunks selected")
        
        document_usecase = DocumentUseCase()
        gstr1_processor = GSTR1Processor()
        
        # Get chunk contents
        chunk_contents = []
        for chunk_id in request.chunk_ids:
            chunk = await document_usecase.get_chunk_by_id(chunk_id)
            if chunk:
                chunk_contents.append(chunk["content"])
        
        if not chunk_contents:
            raise HTTPException(status_code=404, detail="No valid chunks found")
        
        # Pass user GSTIN from request for outward supplies filtering
        user_gstin = request.company_details.gstin if request.company_details else None
        
        # Process chunks and generate summary (local computation only)
        gstr1_data = await gstr1_processor.process_chunks_for_gstr1(chunk_contents, user_gstin)
        
        # Generate a local summary based on the overall_summary data
        overall_summary = gstr1_data.get("gstr1_return", {}).get("overall_summary", {})
        
        summary_text = f"""GSTR-1 Filing Summary:
        
• Total Invoices: {overall_summary.get('total_invoices', 0)}
• Total Taxable Value: ₹{overall_summary.get('total_taxable_value', 0):,.2f}
• Total IGST: ₹{overall_summary.get('total_igst', 0):,.2f}
• Total CGST: ₹{overall_summary.get('total_cgst', 0):,.2f}
• Total SGST: ₹{overall_summary.get('total_sgst', 0):,.2f}
• Total CESS: ₹{overall_summary.get('total_cess', 0):,.2f}
• Total Tax Amount: ₹{overall_summary.get('total_tax', 0):,.2f}
• Total Invoice Value: ₹{overall_summary.get('total_invoice_value', 0):,.2f}

This summary includes only outward supplies where your GSTIN is the seller."""
        
        return {
            "success": True,
            "gstr1_data": gstr1_data,
            "summary": summary_text,
            "processed_chunks": len(chunk_contents)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating GSTR-1 summary: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate summary")
