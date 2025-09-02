"""GSTR-1 filing report generation agent with ADK tool structure."""

import logging
from typing import List, Dict, Any, Optional
import json
import os
from datetime import datetime
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
            logger.info("Google Gemini client initialized for GSTR-1")
        except Exception as e:
            logger.warning(f"Failed to initialize Google client: {e}")
    
    if _groq_client is None and GROQ_AVAILABLE and os.getenv("GROQ_API_KEY"):
        try:
            _groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
            logger.info("Groq client initialized for GSTR-1")
        except Exception as e:
            logger.warning(f"Failed to initialize Groq client: {e}")

# ADK-style tool functions
def get_gstr1_chunks(document_id: Optional[str] = None) -> Dict[str, Any]:
    """Get available document chunks for GSTR-1 processing.
    
    Args:
        document_id: Optional specific document ID to get chunks from
        
    Returns:
        Dict with status, chunks list, and count
    """
    try:
        result = get_document_chunks(document_id)
        
        if result["status"] == "success":
            return {
                "status": "success",
                "chunks": result["chunks"],
                "count": result["count"]
            }
        else:
            return {
                "status": "error",
                "error_message": result.get("error_message", "Failed to get chunks"),
                "chunks": [],
                "count": 0
            }
            
    except Exception as e:
        logger.error(f"Error getting GSTR-1 chunks: {str(e)}")
        return {
            "status": "error",
            "error_message": str(e),
            "chunks": [],
            "count": 0
        }

def process_gstr1_chunks(chunk_ids: List[str]) -> Dict[str, Any]:
    """Process selected chunks in order to extract GSTR-1 relevant data.
    
    Args:
        chunk_ids: List of chunk IDs to process
        
    Returns:
        Dict with status, processed_chunks list, and count
    """
    try:
        # Initialize AI clients
        _initialize_ai_clients()
        
        processed_chunks = []
        
        # Get all chunks first
        chunks_result = get_document_chunks()
        if chunks_result["status"] != "success":
            return {
                "status": "error",
                "error_message": "Failed to retrieve document chunks",
                "processed_chunks": [],
                "count": 0
            }
        
        all_chunks = chunks_result["chunks"]
        
        # Filter and sort selected chunks by their original order
        selected_chunks = []
        for chunk in all_chunks:  # Maintain original order
            if chunk['id'] in chunk_ids:
                selected_chunks.append(chunk)
        
        # Process chunks in order for sequential data extraction
        for i, chunk in enumerate(selected_chunks):
            logger.info(f"Processing chunk {i+1}/{len(selected_chunks)} from {chunk['metadata'].get('file_name', 'Unknown')}")
            
            # Extract GSTR-1 data from chunk with context of previous chunks
            previous_context = ""
            if i > 0:
                previous_context = f"Previous chunks context: {processed_chunks[-1]['gstr1_data'].get('summary', '')}"
            
            gstr1_data = _extract_gstr1_data_from_chunk(chunk['text'], previous_context)
            
            # Log the extraction result for debugging
            logger.info(f"GSTR-1 extraction result for chunk {chunk['id']}: {gstr1_data.get('success', False)}")
            
            processed_chunks.append({
                "chunk_id": chunk['id'],
                "chunk_order": i + 1,
                "source_file": chunk['metadata'].get('file_name', 'Unknown'),
                "gstr1_data": gstr1_data,
                "original_text": chunk['text'][:500] + "..." if len(chunk['text']) > 500 else chunk['text']
            })
        
        return {
            "status": "success",
            "processed_chunks": processed_chunks,
            "count": len(processed_chunks)
        }
        
    except Exception as e:
        logger.error(f"Error processing chunks for GSTR-1: {str(e)}")
        return {
            "status": "error",
            "error_message": str(e),
            "processed_chunks": [],
            "count": 0
        }

def generate_gstr1_summary(processed_chunks: List[Dict[str, Any]], user_header: Dict[str, Any] = None) -> Dict[str, Any]:
    """Generate comprehensive GSTR-1 summary from ordered processed chunks.
    
    Args:
        processed_chunks: List of processed chunk data
        
    Returns:
        Dict with status, gstr1_return, sources_processed, and metadata
    """
    try:
        # Sort chunks by their processing order
        sorted_chunks = sorted(processed_chunks, key=lambda x: x.get('chunk_order', 0))
        
        # Initialize consolidated GSTR-1 return structure with user header if provided
        consolidated_return = {
            "header": {
                "gstin": user_header.get("gstin", "") if user_header else "",
                "trading_name": user_header.get("trading_name", "") if user_header else "",
                "legal_name": user_header.get("legal_name", "") if user_header else "",
                "return_period": user_header.get("return_period", "") if user_header else "",
                "gross_turnover": user_header.get("gross_turnover", 0) if user_header else 0,
                "filing_date": datetime.now().strftime("%Y-%m-%d")
            },
            "b2b_supplies": {"invoices": []},
            "b2cl_supplies": {"invoices": []},
            "b2cs_supplies": {"summary": []},
            "zero_rated_supplies": {"invoices": []},
            "nil_exempt_supplies": {"summary": []},
            "credit_debit_notes": {"notes": []},
            "hsn_summary": {"hsn_wise": []},
            "documents_issued": {
                "invoices": {
                    "from_serial": "",
                    "to_serial": "",
                    "total_issued": 0,
                    "cancelled": 0,
                    "net_issued": 0
                }
            },
            "amendments": {"amended_invoices": []},
            "overall_summary": {
                "total_taxable_value": 0,
                "total_igst": 0,
                "total_cgst": 0,
                "total_sgst": 0,
                "total_cess": 0,
                "total_tax": 0,
                "total_invoice_value": 0
            }
        }
        
        # Aggregate data from all processed chunks
        valid_chunks = 0
        for chunk in sorted_chunks:
            gstr1_data = chunk.get('gstr1_data', {})
            
            # Check if chunk has valid GSTR-1 data
            if gstr1_data.get('success') and gstr1_data.get('data'):
                valid_chunks += 1
                chunk_data = gstr1_data['data']
                
                # Handle both nested and flat data structures
                if 'gstr1_return' in chunk_data:
                    chunk_data = chunk_data['gstr1_return']
                
                # Update header with first valid data found
                if chunk_data.get('header', {}).get('gstin') and not consolidated_return['header']['gstin']:
                    consolidated_return['header'].update(chunk_data['header'])
                
                # Aggregate B2B supplies
                if chunk_data.get('b2b_supplies', {}).get('invoices'):
                    consolidated_return['b2b_supplies']['invoices'].extend(chunk_data['b2b_supplies']['invoices'])
                
                # Aggregate B2CL supplies
                if chunk_data.get('b2cl_supplies', {}).get('invoices'):
                    consolidated_return['b2cl_supplies']['invoices'].extend(chunk_data['b2cl_supplies']['invoices'])
                
                # Aggregate B2CS supplies
                if chunk_data.get('b2cs_supplies', {}).get('summary'):
                    consolidated_return['b2cs_supplies']['summary'].extend(chunk_data['b2cs_supplies']['summary'])
                
                # Aggregate HSN summary - keep all products separately (no deduplication)
                if chunk_data.get('hsn_summary', {}).get('hsn_wise'):
                    consolidated_return['hsn_summary']['hsn_wise'].extend(chunk_data['hsn_summary']['hsn_wise'])
                
                # Aggregate overall summary totals
                if chunk_data.get('overall_summary'):
                    summary = chunk_data['overall_summary']
                    consolidated_return['overall_summary']['total_taxable_value'] += summary.get('total_taxable_value', 0)
                    consolidated_return['overall_summary']['total_igst'] += summary.get('total_igst', 0)
                    consolidated_return['overall_summary']['total_cgst'] += summary.get('total_cgst', 0)
                    consolidated_return['overall_summary']['total_sgst'] += summary.get('total_sgst', 0)
                    consolidated_return['overall_summary']['total_cess'] += summary.get('total_cess', 0)
                    consolidated_return['overall_summary']['total_tax'] += summary.get('total_tax', 0)
                    consolidated_return['overall_summary']['total_invoice_value'] += summary.get('total_invoice_value', 0)
        
        # If no valid chunks found, return error
        if valid_chunks == 0:
            return {
                "status": "error",
                "error_message": "No valid GSTR-1 data found in processed chunks",
                "gstr1_return": None,
                "sources_processed": 0
            }
        
        # Remove duplicate invoices (same Invoice No + Date + GSTIN)
        seen_invoices = set()
        unique_b2b_invoices = []
        for invoice in consolidated_return['b2b_supplies']['invoices']:
            invoice_key = (
                invoice.get('invoice_no', ''),
                invoice.get('date', ''),
                invoice.get('customer_gstin', '')
            )
            if invoice_key not in seen_invoices:
                seen_invoices.add(invoice_key)
                unique_b2b_invoices.append(invoice)
        
        consolidated_return['b2b_supplies']['invoices'] = unique_b2b_invoices
        
        # Validate user GSTIN against document GSTINs if provided
        if user_header and user_header.get('gstin'):
            user_gstin = user_header['gstin']
            document_gstins = set()
            
            # Collect all GSTINs from processed chunks
            for chunk in sorted_chunks:
                gstr1_data = chunk.get('gstr1_data', {})
                if gstr1_data.get('success') and gstr1_data.get('data'):
                    chunk_data = gstr1_data['data']
                    if 'gstr1_return' in chunk_data:
                        chunk_data = chunk_data['gstr1_return']
                    
                    if chunk_data.get('header', {}).get('gstin'):
                        document_gstins.add(chunk_data['header']['gstin'])
            
            # Check if user GSTIN matches any document GSTIN
            if document_gstins and user_gstin not in document_gstins:
                return {
                    "status": "error",
                    "error_message": f"User GSTIN {user_gstin} does not match document GSTINs: {', '.join(document_gstins)}",
                    "gstr1_return": None,
                    "sources_processed": 0
                }
        
        # Keep all HSN products separately - no deduplication
        # HSN summary already aggregated above without deduplication
        
        return {
            "status": "success",
            "gstr1_return": consolidated_return,
            "sources_processed": len(sorted_chunks),
            "chunks_processed": [f"{chunk['source_file']} (Chunk {chunk.get('chunk_order', 0)})" for chunk in sorted_chunks],
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating GSTR-1 summary: {str(e)}")
        return {
            "status": "error",
            "error_message": str(e),
            "gstr1_return": None,
            "sources_processed": 0
        }

def _extract_gstr1_data_from_chunk(text: str, previous_context: str = "") -> Dict[str, Any]:
    """Extract GSTR-1 relevant data from a text chunk using AI."""
    prompt = _build_gstr1_extraction_prompt(text, previous_context)
    
    # Try Google Gemini first
    if _google_client:
        try:
            response = _google_client.generate_content(prompt)
            return _parse_gstr1_response(response.text)
        except Exception as e:
            logger.warning(f"Google Gemini failed for GSTR-1 extraction: {e}")
    
    # Fallback to Groq
    if _groq_client:
        try:
            response = _groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.1,
                max_tokens=2000
            )
            return _parse_gstr1_response(response.choices[0].message.content)
        except Exception as e:
            logger.warning(f"Groq failed for GSTR-1 extraction: {e}")
    
    return {"success": False, "error": "No AI service available"}

def _build_gstr1_extraction_prompt(text: str, previous_context: str = "") -> str:
    """Build prompt for GSTR-1 data extraction with context from previous chunks."""
    context_section = ""
    if previous_context:
        context_section = f"""
### Context from Previous Chunks:
{previous_context}

Use this context to maintain consistency and build upon previous data extraction.
"""

    return f"""You are an expert GST data extraction assistant. Extract ALL invoice and tax details from the document.
{context_section}
### CRITICAL: Extract COMPLETE invoice data including:
- Invoice numbers, dates, customer details
- ALL line items with descriptions, quantities, rates
- HSN codes, tax rates, tax amounts
- Customer GSTIN, place of supply
- NEVER leave fields empty if data exists

### JSON Schema (MANDATORY):
{{
  "gstr1_return": {{
    "header": {{"gstin": "seller_gstin_from_document", "trading_name": "company_name", "legal_name": "legal_company_name", "return_period": "YYYY-MM", "filing_date": "YYYY-MM-DD"}},
    "b2b_supplies": {{
      "invoices": [{{
        "invoice_no": "invoice_number",
        "invoice_date": "YYYY-MM-DD",
        "customer_gstin": "buyer_gstin",
        "customer_name": "buyer_name",
        "pos": "place_of_supply_state_code",
        "reverse_charge": "N",
        "invoice_type": "Regular",
        "line_items": [{{
          "description": "item_description",
          "hsn_code": "hsn_code",
          "quantity": number,
          "unit": "unit_type",
          "rate": number,
          "taxable_value": number,
          "igst_rate": number,
          "igst_amount": number,
          "cgst_rate": number,
          "cgst_amount": number,
          "sgst_rate": number,
          "sgst_amount": number,
          "cess_rate": 0,
          "cess_amount": 0
        }}]
      }}]
    }},
    "hsn_summary": {{
      "hsn_wise": [{{
        "hsn_code": "hsn_code",
        "description": "item_description",
        "uqc": "unit_type",
        "total_quantity": number,
        "total_taxable_value": number,
        "igst_amount": number,
        "cgst_amount": number,
        "sgst_amount": number,
        "cess_amount": 0
      }}]
    }},
    "overall_summary": {{
      "total_taxable_value": sum_of_all_taxable_values,
      "total_igst": sum_of_all_igst,
      "total_cgst": sum_of_all_cgst,
      "total_sgst": sum_of_all_sgst,
      "total_cess": 0,
      "total_tax": sum_of_all_taxes,
      "total_invoice_value": taxable_value_plus_taxes
    }}
  }},
  "summary": "Extracted X invoices with Y line items"
}}

### EXTRACTION RULES:
- Extract EVERY invoice and line item completely
- Calculate accurate tax totals and summary values
- Use actual dates, amounts, and codes from document
- If B2CL/B2CS/other sections have data, include them
- Return valid JSON only, no explanations

Document content to analyze:
{text}

Extract all GST-related information and return as JSON following the exact schema above."""

def _parse_gstr1_response(response_text: str) -> Dict[str, Any]:
    """Parse AI response to extract GSTR-1 data."""
    try:
        # Clean the response text and extract JSON
        response_text = response_text.strip()
        
        # Try to find and extract the first complete JSON object
        start_idx = response_text.find('{')
        if start_idx == -1:
            return {
                "success": False,
                "error": "No JSON object found in response"
            }
        
        # Find the matching closing brace by counting braces
        brace_count = 0
        end_idx = start_idx
        for i in range(start_idx, len(response_text)):
            if response_text[i] == '{':
                brace_count += 1
            elif response_text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    end_idx = i + 1
                    break
        
        if brace_count != 0:
            return {
                "success": False,
                "error": "Incomplete JSON object in response"
            }
        
        json_str = response_text[start_idx:end_idx]
        parsed_data = json.loads(json_str)
        
        return {
            "success": True,
            "data": parsed_data
        }
            
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {e}")
        return {
            "success": False,
            "error": f"JSON parsing failed: {str(e)}"
        }
    except Exception as e:
        logger.error(f"Error parsing GSTR-1 response: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def _generate_final_gstr1_return(full_context: str, chunk_context: str) -> Dict[str, Any]:
    """Generate final GSTR-1 return using all chunks in order."""
    prompt = f"""You are an expert GST consultant generating a complete GSTR-1 return.
Process ALL the document chunks in order to create a comprehensive GSTR-1 filing.

### Context from Previous Chunk Processing:
{chunk_context}

### Complete Document Content (All Chunks in Order):
{full_context}

### Task:
Generate a complete GSTR-1 return by processing ALL chunks sequentially and consolidating the data.

### Required JSON Schema:
{{
  "header": {{"gstin": "string", "trading_name": "string", "legal_name": "string", "return_period": "YYYY-MM", "filing_date": "YYYY-MM-DD"}},
  "b2b_supplies": {{"invoices": []}},
  "b2cl_supplies": {{"invoices": []}}, 
  "b2cs_supplies": {{"summary": []}},
  "zero_rated_supplies": {{"invoices": []}},
  "nil_exempt_supplies": {{"summary": []}},
  "credit_debit_notes": {{"notes": []}},
  "hsn_summary": {{"hsn_wise": []}},
  "documents_issued": {{"invoices": {{"from_serial": "", "to_serial": "", "total_issued": 0, "cancelled": 0, "net_issued": 0}}}},
  "amendments": {{"amended_invoices": []}},
  "overall_summary": {{"total_taxable_value": 0, "total_igst": 0, "total_cgst": 0, "total_sgst": 0, "total_cess": 0, "total_tax": 0, "total_invoice_value": 0}}
}}

### Instructions:
- Process chunks in sequential order to build complete picture
- Extract all invoice details, tax amounts, customer information
- Calculate totals across all chunks
- Return only valid JSON, no extra text
- Use actual data from documents, not placeholder values"""

    # Try Google Gemini first
    if _google_client:
        try:
            response = _google_client.generate_content(prompt)
            parsed = _parse_gstr1_response(response.text)
            if parsed.get('success'):
                return parsed['data']
        except Exception as e:
            logger.warning(f"Google Gemini failed for final GSTR-1 generation: {e}")
    
    # Fallback to Groq
    if _groq_client:
        try:
            response = _groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.1-8b-instant",
                temperature=0.1,
                max_tokens=3000
            )
            parsed = _parse_gstr1_response(response.choices[0].message.content)
            if parsed.get('success'):
                return parsed['data']
        except Exception as e:
            logger.warning(f"Groq failed for final GSTR-1 generation: {e}")
    
    # Fallback to basic structure
    return _get_empty_gstr1_structure()

def _get_empty_gstr1_structure() -> Dict[str, Any]:
    """Get empty GSTR-1 structure as fallback."""
    return {
        "header": {
            "gstin": "",
            "trading_name": "",
            "legal_name": "",
            "return_period": datetime.now().strftime("%Y-%m"),
            "filing_date": datetime.now().strftime("%Y-%m-%d")
        },
        "b2b_supplies": {"invoices": []},
        "b2cl_supplies": {"invoices": []},
        "b2cs_supplies": {"summary": []},
        "zero_rated_supplies": {"invoices": []},
        "nil_exempt_supplies": {"summary": []},
        "credit_debit_notes": {"notes": []},
        "hsn_summary": {"hsn_wise": []},
        "documents_issued": {
            "invoices": {
                "from_serial": "",
                "to_serial": "",
                "total_issued": 0,
                "cancelled": 0,
                "net_issued": 0
            }
        },
        "amendments": {"amended_invoices": []},
        "overall_summary": {
            "total_taxable_value": 0,
            "total_igst": 0,
            "total_cgst": 0,
            "total_sgst": 0,
            "total_cess": 0,
            "total_tax": 0,
            "total_invoice_value": 0
        }
    }

# Legacy wrapper class for backward compatibility
class GSTR1Agent:
    """Legacy wrapper for GSTR-1 operations - use ADK tool functions directly."""
    
    def __init__(self, document_agent=None):
        self.document_agent = document_agent
        # Initialize AI clients
        _initialize_ai_clients()
        self.google_client = _google_client
        self.groq_client = _groq_client
    
    async def get_document_chunks(self, document_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Legacy method - use get_gstr1_chunks function directly."""
        result = get_gstr1_chunks(document_id)
        return result.get("chunks", [])
    
    async def process_chunks_for_gstr1(self, chunk_ids: List[str]) -> List[Dict[str, Any]]:
        """Legacy method - use process_gstr1_chunks function directly."""
        result = process_gstr1_chunks(chunk_ids)
        return result.get("processed_chunks", [])
    
    async def generate_gstr1_summary(self, processed_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Legacy method - use generate_gstr1_summary function directly."""
        return generate_gstr1_summary(processed_chunks)
