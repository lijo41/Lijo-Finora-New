"""GSTR-1 data extraction processor using Groq AI."""

import json
import logging
from typing import Dict, Any, List
from datetime import datetime
import re
from groq import Groq
from utils.config import GROQ_API_KEY

logger = logging.getLogger(__name__)

class GSTR1Processor:
    """Processes documents to extract GSTR-1 filing data using Groq AI."""
    
    def __init__(self):
        self.groq_client = Groq(api_key=GROQ_API_KEY)
        self.model = "llama-3.1-8b-instant"
        
    def get_gstr1_extraction_prompt(self) -> str:
        """Returns the system prompt for GSTR-1 data extraction."""
        return """You are an assistant that extracts structured data for GSTR-1 filing.  
Your task is to convert the provided document details into a fixed JSON schema.  

### Rules:
- Always return a JSON object following this schema:
{
  "gstr1_return": {
    "header": {
      "gstin": "",
      "return_period": "",
      "filing_date": "",
      "legal_name": "",
      "trade_name": ""
    },
    "b2b_supplies": {
      "invoices": [
        {
          "invoice_number": "",
          "invoice_date": "",
          "seller_gstin": "",
          "customer_gstin": "",
          "customer_name": "",
          "place_of_supply": "",
          "reverse_charge": false,
          "invoice_type": "Regular",
          "items": [
            {
              "description": "",
              "hsn_code": "",
              "quantity": 0,
              "unit": "",
              "rate": 0,
              "taxable_value": 0,
              "igst_rate": 0,
              "igst_amount": 0,
              "cgst_rate": 0,
              "cgst_amount": 0,
              "sgst_rate": 0,
              "sgst_amount": 0,
              "cess_rate": 0,
              "cess_amount": 0
            }
          ],
          "total_taxable_value": 0,
          "total_tax": 0,
          "invoice_value": 0
        }
      ]
    },
    "b2cl_supplies": {
      "invoices": []
    },
    "b2cs_supplies": {
      "summary": [
        {
          "place_of_supply": "",
          "rate": 0,
          "taxable_value": 0,
          "igst_amount": 0,
          "cgst_amount": 0,
          "sgst_amount": 0,
          "cess_amount": 0
        }
      ]
    },
    "zero_rated_supplies": {
      "invoices": []
    },
    "nil_exempt_supplies": {
      "summary": [
        {
          "description": "",
          "nil_rated_amount": 0,
          "exempted_amount": 0,
          "non_gst_amount": 0
        }
      ]
    },
    "credit_debit_notes": {
      "notes": []
    },
    "hsn_summary": {
      "items": [
        {
          "hsn_code": "",
          "description": "",
          "uqc": "",
          "total_quantity": 0,
          "total_value": 0,
          "taxable_value": 0,
          "igst_amount": 0,
          "cgst_amount": 0,
          "sgst_amount": 0,
          "cess_amount": 0
        }
      ]
    },
    "documents_issued": {
      "invoices": {
        "from_serial": "",
        "to_serial": "",
        "total_number": 0,
        "cancelled": 0
      },
      "credit_notes": {
        "from_serial": "",
        "to_serial": "",
        "total_number": 0,
        "cancelled": 0
      },
      "debit_notes": {
        "from_serial": "",
        "to_serial": "",
        "total_number": 0,
        "cancelled": 0
      }
    },
    "amendments": {
      "invoices": []
    },
    "overall_summary": {
      "total_taxable_value": 0,
      "total_igst": 0,
      "total_cgst": 0,
      "total_sgst": 0,
      "total_cess": 0,
      "total_tax": 0,
      "total_invoice_value": 0,
      "total_invoices": 0
    }
  }
}
- If any section has no data → return it with an empty array or zero values (do not remove the section).
- Dates must be in YYYY-MM-DD format.
- Amounts should be numbers (not strings).
- HSN summary must aggregate quantities & values per HSN code.
- Totals must be consistent: taxable_value + tax = invoice_value.
- Do not include extra commentary, only valid JSON.

### Example Input:
Invoice No: GST-4525-26  
Date: 24-Aug-2025  
Customer GSTIN: 32AACCB1122B1ZB  
Items: Hitachi Drill (2 Nos @ 3500), Makita Grinder (1 Nos @ 4800)  
Tax: 18% IGST  

### Example Output:
{
  "gstr1_return": {
    "header": {
      "gstin": "",
      "return_period": "2025-08",
      "filing_date": "",
      "legal_name": "",
      "trade_name": ""
    },
    "b2b_supplies": {
      "invoices": [
        {
          "invoice_number": "GST-4525-26",
          "invoice_date": "2025-08-24",
          "customer_gstin": "32AACCB1122B1ZB",
          "customer_name": "",
          "place_of_supply": "",
          "reverse_charge": false,
          "invoice_type": "Regular",
          "items": [
            {
              "description": "Hitachi Drill",
              "hsn_code": "",
              "quantity": 2,
              "unit": "Nos",
              "rate": 3500,
              "taxable_value": 7000,
              "igst_rate": 18,
              "igst_amount": 1260,
              "cgst_rate": 0,
              "cgst_amount": 0,
              "sgst_rate": 0,
              "sgst_amount": 0,
              "cess_rate": 0,
              "cess_amount": 0
            },
            {
              "description": "Makita Grinder",
              "hsn_code": "",
              "quantity": 1,
              "unit": "Nos",
              "rate": 4800,
              "taxable_value": 4800,
              "igst_rate": 18,
              "igst_amount": 864,
              "cgst_rate": 0,
              "cgst_amount": 0,
              "sgst_rate": 0,
              "sgst_amount": 0,
              "cess_rate": 0,
              "cess_amount": 0
            }
          ],
          "total_taxable_value": 11800,
          "total_tax": 2124,
          "invoice_value": 13924
        }
      ]
    },
    "b2cl_supplies": {"invoices": []},
    "b2cs_supplies": {"summary": []},
    "zero_rated_supplies": {"invoices": []},
    "nil_exempt_supplies": {"summary": []},
    "credit_debit_notes": {"notes": []},
    "hsn_summary": {"items": []},
    "documents_issued": {
      "invoices": {"from_serial": "", "to_serial": "", "total_number": 0, "cancelled": 0},
      "credit_notes": {"from_serial": "", "to_serial": "", "total_number": 0, "cancelled": 0},
      "debit_notes": {"from_serial": "", "to_serial": "", "total_number": 0, "cancelled": 0}
    },
    "amendments": {"invoices": []},
    "overall_summary": {
      "total_taxable_value": 11800,
      "total_igst": 2124,
      "total_cgst": 0,
      "total_sgst": 0,
      "total_cess": 0,
      "total_tax": 2124,
      "total_invoice_value": 13924,
      "total_invoices": 1
    }
  }
}"""

    async def process_chunk_for_gstr1(self, chunk_content: str) -> Dict[str, Any]:
        """Process a document chunk to extract GSTR-1 relevant data using Groq for JSON extraction only."""
        try:
            messages = [
                {
                    "role": "system",
                    "content": self.get_gstr1_extraction_prompt()
                },
                {
                    "role": "user", 
                    "content": f"Extract GSTR-1 data from this document content:\n\n{chunk_content}"
                }
            ]
            
            # Use Groq only for JSON extraction from document content
            response = self.groq_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,
                max_tokens=4000
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Try to parse the JSON response
            try:
                result = json.loads(result_text)
                return result
            except json.JSONDecodeError:
                # If direct parsing fails, try to extract JSON from the response
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    return result
                else:
                    logger.error(f"Failed to parse JSON from Groq response: {result_text}")
                    return self._get_empty_gstr1_structure()
                    
        except Exception as e:
            logger.error(f"Error processing chunk for GSTR-1: {str(e)}")
            return self._get_empty_gstr1_structure()
    
    def _get_empty_gstr1_structure(self) -> Dict[str, Any]:
        """Returns an empty GSTR-1 structure."""
        return {
            "gstr1_return": {
                "header": {
                    "gstin": "",
                    "return_period": "",
                    "filing_date": "",
                    "legal_name": "",
                    "trade_name": ""
                },
                "b2b_supplies": {"invoices": []},
                "b2cl_supplies": {"invoices": []},
                "b2cs_supplies": {"summary": []},
                "zero_rated_supplies": {"invoices": []},
                "nil_exempt_supplies": {"summary": []},
                "credit_debit_notes": {"notes": []},
                "hsn_summary": {"items": []},
                "documents_issued": {
                    "invoices": {"from_serial": "", "to_serial": "", "total_number": 0, "cancelled": 0},
                    "credit_notes": {"from_serial": "", "to_serial": "", "total_number": 0, "cancelled": 0},
                    "debit_notes": {"from_serial": "", "to_serial": "", "total_number": 0, "cancelled": 0}
                },
                "amendments": {"invoices": []},
                "overall_summary": {
                    "total_taxable_value": 0,
                    "total_igst": 0,
                    "total_cgst": 0,
                    "total_sgst": 0,
                    "total_cess": 0,
                    "total_tax": 0,
                    "total_invoice_value": 0,
                    "total_invoices": 0
                }
            }
        }
    
    def merge_gstr1_data(self, gstr1_results: List[Dict[str, Any]], user_gstin: str = None) -> Dict[str, Any]:
        """Merge multiple GSTR-1 extraction results into a consolidated return using local computation (no Groq)."""
        if not gstr1_results:
            return self._get_empty_gstr1_structure()
        
        merged = self._get_empty_gstr1_structure()
        
        # Merge data from all results using local logic
        for result in gstr1_results:
            if "gstr1_return" not in result:
                continue
            
            gstr1_data = result["gstr1_return"]
            
            # Merge header information (use first non-empty values)
            for key, value in gstr1_data.get("header", {}).items():
                if value and not merged["gstr1_return"]["header"][key]:
                    merged["gstr1_return"]["header"][key] = value
            
            # Merge B2B invoices
            if "b2b_supplies" in gstr1_data and "invoices" in gstr1_data["b2b_supplies"]:
                merged["gstr1_return"]["b2b_supplies"]["invoices"].extend(
                    gstr1_data["b2b_supplies"]["invoices"]
                )
            
            # Merge B2CL invoices
            if "b2cl_supplies" in gstr1_data and "invoices" in gstr1_data["b2cl_supplies"]:
                merged["gstr1_return"]["b2cl_supplies"]["invoices"].extend(
                    gstr1_data["b2cl_supplies"]["invoices"]
                )
            
            # Merge B2CS summary
            if "b2cs_supplies" in gstr1_data and "summary" in gstr1_data["b2cs_supplies"]:
                merged["gstr1_return"]["b2cs_supplies"]["summary"].extend(
                    gstr1_data["b2cs_supplies"]["summary"]
                )
            
            # Merge other sections similarly
            for section in ["zero_rated_supplies", "nil_exempt_supplies", "credit_debit_notes", "amendments"]:
                if section in gstr1_data:
                    section_data = gstr1_data[section]
                    if isinstance(section_data, dict):
                        for key, value in section_data.items():
                            if isinstance(value, list):
                                merged["gstr1_return"][section][key].extend(value)
        
        # Remove duplicate invoices after merging
        merged = self._remove_duplicate_invoices(merged)
        
        # Calculate HSN summary and overall summary using local computation
        merged["gstr1_return"]["hsn_summary"] = self._calculate_hsn_summary(merged, user_gstin)
        merged["gstr1_return"]["overall_summary"] = self._calculate_overall_summary(merged, user_gstin)
        
        return merged
    
    def _remove_duplicate_invoices(self, merged_data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove duplicate invoices based on invoice_no + customer_gstin + invoice_date."""
        
        # Remove duplicates from B2B supplies
        merged_data["gstr1_return"]["b2b_supplies"]["invoices"] = self._deduplicate_invoice_list(
            merged_data["gstr1_return"]["b2b_supplies"]["invoices"]
        )
        
        # Remove duplicates from B2CL supplies
        merged_data["gstr1_return"]["b2cl_supplies"]["invoices"] = self._deduplicate_invoice_list(
            merged_data["gstr1_return"]["b2cl_supplies"]["invoices"]
        )
        
        # Remove duplicates from Zero-rated supplies
        if "zero_rated_supplies" in merged_data["gstr1_return"] and "invoices" in merged_data["gstr1_return"]["zero_rated_supplies"]:
            merged_data["gstr1_return"]["zero_rated_supplies"]["invoices"] = self._deduplicate_invoice_list(
                merged_data["gstr1_return"]["zero_rated_supplies"]["invoices"]
            )
        
        return merged_data
    
    def _deduplicate_invoice_list(self, invoices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate invoices from a list based on invoice_no + customer_gstin + invoice_date."""
        seen_invoices = set()
        unique_invoices = []
        
        for invoice in invoices:
            # Create a unique key based on invoice_no, customer_gstin, and invoice_date
            invoice_key = (
                invoice.get("invoice_no", ""),
                invoice.get("customer_gstin", ""),
                invoice.get("invoice_date", "")
            )
            
            # Only add if we haven't seen this combination before
            if invoice_key not in seen_invoices:
                seen_invoices.add(invoice_key)
                unique_invoices.append(invoice)
        
        return unique_invoices
    
    def _calculate_hsn_summary(self, merged_data: Dict[str, Any], user_gstin: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """Calculate HSN summary from outward supplies only (invoices where user's GSTIN is the seller)."""
        hsn_items = []
        
        # Process B2B invoices (outward supplies only)
        for invoice in merged_data["gstr1_return"]["b2b_supplies"]["invoices"]:
            # Only include invoices where user is the seller (outward supplies)
            seller_gstin = invoice.get("seller_gstin", "")
            if user_gstin and seller_gstin and seller_gstin != user_gstin:
                continue  # Skip invoices where user is not the seller
                
            for item in invoice.get("items", []):
                hsn_code = item.get("hsn_code", "")
                
                # Create individual entry for each product
                hsn_entry = {
                    "hsn_code": hsn_code,
                    "description": item.get("description", ""),
                    "uqc": item.get("unit", ""),
                    "total_quantity": item.get("quantity", 0),
                    "taxable_value": item.get("taxable_value", 0),
                    "igst_amount": item.get("igst_amount", 0),
                    "cgst_amount": item.get("cgst_amount", 0),
                    "sgst_amount": item.get("sgst_amount", 0),
                    "cess_amount": item.get("cess_amount", 0),
                    "total_value": item.get("taxable_value", 0) + item.get("igst_amount", 0) + 
                                 item.get("cgst_amount", 0) + item.get("sgst_amount", 0) + 
                                 item.get("cess_amount", 0)
                }
                hsn_items.append(hsn_entry)
        
        # Process B2CL invoices
        for invoice in merged_data["gstr1_return"]["b2cl_supplies"]["invoices"]:
            for item in invoice.get("items", []):
                hsn_code = item.get("hsn_code", "")
                
                hsn_entry = {
                    "hsn_code": hsn_code,
                    "description": item.get("description", ""),
                    "uqc": item.get("unit", ""),
                    "total_quantity": item.get("quantity", 0),
                    "taxable_value": item.get("taxable_value", 0),
                    "igst_amount": item.get("igst_amount", 0),
                    "cgst_amount": item.get("cgst_amount", 0),
                    "sgst_amount": item.get("sgst_amount", 0),
                    "cess_amount": item.get("cess_amount", 0),
                    "total_value": item.get("taxable_value", 0) + item.get("igst_amount", 0) + 
                                 item.get("cgst_amount", 0) + item.get("sgst_amount", 0) + 
                                 item.get("cess_amount", 0)
                }
                hsn_items.append(hsn_entry)
        
        # Process Zero-rated supplies (outward supplies only)
        for invoice in merged_data["gstr1_return"]["zero_rated_supplies"]["invoices"]:
            # Only include invoices where user is the seller (outward supplies)
            seller_gstin = invoice.get("seller_gstin", "")
            if user_gstin and seller_gstin and seller_gstin != user_gstin:
                continue  # Skip invoices where user is not the seller
                
            for item in invoice.get("items", []):
                hsn_code = item.get("hsn_code", "")
                
                hsn_entry = {
                    "hsn_code": hsn_code,
                    "description": item.get("description", ""),
                    "uqc": item.get("unit", ""),
                    "total_quantity": item.get("quantity", 0),
                    "taxable_value": item.get("taxable_value", 0),
                    "igst_amount": item.get("igst_amount", 0),
                    "cgst_amount": item.get("cgst_amount", 0),
                    "sgst_amount": item.get("sgst_amount", 0),
                    "cess_amount": item.get("cess_amount", 0),
                    "total_value": item.get("taxable_value", 0) + item.get("igst_amount", 0) + 
                                 item.get("cgst_amount", 0) + item.get("sgst_amount", 0) + 
                                 item.get("cess_amount", 0)
                }
                hsn_items.append(hsn_entry)
        
        return {"items": hsn_items}
    
    def _calculate_overall_summary(self, merged_data: Dict[str, Any], user_gstin: str = None) -> Dict[str, Any]:
        """Calculate overall summary from outward supplies only (invoices where user's GSTIN is the seller)."""
        summary = {
            "total_taxable_value": 0,
            "total_igst": 0,
            "total_cgst": 0,
            "total_sgst": 0,
            "total_cess": 0,
            "total_tax": 0,
            "total_invoice_value": 0,
            "total_invoices": 0
        }
        
        # Sum from B2B supplies (outward supplies only - where user's GSTIN is the seller)
        for invoice in merged_data["gstr1_return"]["b2b_supplies"]["invoices"]:
            # Only include invoices where user is the seller (outward supplies)
            seller_gstin = invoice.get("seller_gstin", "")
            if user_gstin and seller_gstin and seller_gstin != user_gstin:
                continue  # Skip invoices where user is not the seller
                
            summary["total_taxable_value"] += invoice.get("total_taxable_value", 0)
            summary["total_invoice_value"] += invoice.get("invoice_value", 0)
            summary["total_invoices"] += 1
            
            for item in invoice.get("items", []):
                summary["total_igst"] += item.get("igst_amount", 0)
                summary["total_cgst"] += item.get("cgst_amount", 0)
                summary["total_sgst"] += item.get("sgst_amount", 0)
                summary["total_cess"] += item.get("cess_amount", 0)
        
        # Sum from B2CL supplies (outward supplies to large unregistered customers)
        for invoice in merged_data["gstr1_return"]["b2cl_supplies"]["invoices"]:
            # Only include invoices where user is the seller (outward supplies)
            seller_gstin = invoice.get("seller_gstin", "")
            if user_gstin and seller_gstin and seller_gstin != user_gstin:
                continue  # Skip invoices where user is not the seller
                
            summary["total_taxable_value"] += invoice.get("total_taxable_value", 0)
            summary["total_invoice_value"] += invoice.get("invoice_value", 0)
            summary["total_invoices"] += 1
            
            for item in invoice.get("items", []):
                summary["total_igst"] += item.get("igst_amount", 0)
                summary["total_cgst"] += item.get("cgst_amount", 0)
                summary["total_sgst"] += item.get("sgst_amount", 0)
                summary["total_cess"] += item.get("cess_amount", 0)
        
        # Sum from B2CS supplies (outward supplies to small unregistered customers)
        for item in merged_data["gstr1_return"]["b2cs_supplies"]["summary"]:
            summary["total_taxable_value"] += item.get("taxable_value", 0)
            summary["total_igst"] += item.get("igst_amount", 0)
            summary["total_cgst"] += item.get("cgst_amount", 0)
            summary["total_sgst"] += item.get("sgst_amount", 0)
            summary["total_cess"] += item.get("cess_amount", 0)
        
        # Sum from Zero-rated supplies (exports - outward supplies)
        for invoice in merged_data["gstr1_return"]["zero_rated_supplies"]["invoices"]:
            # Only include invoices where user is the seller (outward supplies)
            seller_gstin = invoice.get("seller_gstin", "")
            if user_gstin and seller_gstin and seller_gstin != user_gstin:
                continue  # Skip invoices where user is not the seller
                
            summary["total_taxable_value"] += invoice.get("taxable_value", 0)
            summary["total_invoice_value"] += invoice.get("invoice_value", 0)
            summary["total_invoices"] += 1
        
        # Calculate total tax
        summary["total_tax"] = (summary["total_igst"] + summary["total_cgst"] + 
                              summary["total_sgst"] + summary["total_cess"])
        
        return summary

    def _remove_duplicate_invoices(self, merged_data: Dict[str, Any]) -> Dict[str, Any]:
        """Remove duplicate invoices based on invoice_no + customer_gstin + invoice_date."""
        
        # Remove duplicates from B2B supplies
        merged_data["gstr1_return"]["b2b_supplies"]["invoices"] = self._deduplicate_invoice_list(
            merged_data["gstr1_return"]["b2b_supplies"]["invoices"]
        )
        
        # Remove duplicates from B2CL supplies
        merged_data["gstr1_return"]["b2cl_supplies"]["invoices"] = self._deduplicate_invoice_list(
            merged_data["gstr1_return"]["b2cl_supplies"]["invoices"]
        )
        
        # Remove duplicates from Zero-rated supplies
        if "zero_rated_supplies" in merged_data["gstr1_return"] and "invoices" in merged_data["gstr1_return"]["zero_rated_supplies"]:
            merged_data["gstr1_return"]["zero_rated_supplies"]["invoices"] = self._deduplicate_invoice_list(
                merged_data["gstr1_return"]["zero_rated_supplies"]["invoices"]
            )
        
        return merged_data

    def _deduplicate_invoice_list(self, invoices: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate invoices from a list based on invoice_no + customer_gstin + invoice_date."""
        seen_invoices = set()
        unique_invoices = []
        
        for invoice in invoices:
            # Create a unique key based on invoice_no, customer_gstin, and invoice_date
            invoice_key = (
                invoice.get("invoice_no", ""),
                invoice.get("customer_gstin", ""),
                invoice.get("invoice_date", "")
            )
            
            # Only add if we haven't seen this combination before
            if invoice_key not in seen_invoices:
                seen_invoices.add(invoice_key)
                unique_invoices.append(invoice)
        
        return unique_invoices

    def _calculate_hsn_summary(self, merged_data: Dict[str, Any], user_gstin: str = None) -> Dict[str, List[Dict[str, Any]]]:
        """Calculate HSN summary from outward supplies only (invoices where user's GSTIN is the seller)."""
        hsn_items = []
        
        # Process B2B invoices (outward supplies only)
        for invoice in merged_data["gstr1_return"]["b2b_supplies"]["invoices"]:
            # Only include invoices where user is the seller (outward supplies)
            seller_gstin = invoice.get("seller_gstin", "")
            if user_gstin and seller_gstin and seller_gstin != user_gstin:
                continue  # Skip invoices where user is not the seller
                
            for item in invoice.get("items", []):
                hsn_code = item.get("hsn_code", "")
                
                # Create individual entry for each product
                hsn_entry = {
                    "hsn_code": hsn_code,
                    "description": item.get("description", ""),
                    "uqc": item.get("unit", ""),
                    "total_quantity": item.get("quantity", 0),
                    "taxable_value": item.get("taxable_value", 0),
                    "igst_amount": item.get("igst_amount", 0),
                    "cgst_amount": item.get("cgst_amount", 0),
                    "sgst_amount": item.get("sgst_amount", 0),
                    "cess_amount": item.get("cess_amount", 0),
                    "total_value": item.get("taxable_value", 0) + item.get("igst_amount", 0) +
                                 item.get("cgst_amount", 0) + item.get("sgst_amount", 0) + 
                                 item.get("cess_amount", 0)
                }
                hsn_items.append(hsn_entry)
        
        return {"items": hsn_items}
        for item in invoice.get("items", []):
            hsn_code = item.get("hsn_code", "")
            
            hsn_entry = {
                "hsn_code": hsn_code,
                "description": item.get("description", ""),
                "uqc": item.get("unit", ""),
                "total_quantity": item.get("quantity", 0),
                "taxable_value": item.get("taxable_value", 0),
                "igst_amount": item.get("igst_amount", 0),
                "cgst_amount": item.get("cgst_amount", 0),
                "sgst_amount": item.get("sgst_amount", 0),
                "cess_amount": item.get("cess_amount", 0),
                "total_value": item.get("taxable_value", 0) + item.get("igst_amount", 0) + 
                             item.get("cgst_amount", 0) + item.get("sgst_amount", 0) + 
                             item.get("cess_amount", 0)
            }
            hsn_items.append(hsn_entry)
    
    # Process Zero-rated supplies (outward supplies only)
    for invoice in merged_data["gstr1_return"]["zero_rated_supplies"]["invoices"]:
        # Only include invoices where user is the seller (outward supplies)
        seller_gstin = invoice.get("seller_gstin", "")
        if user_gstin and seller_gstin and seller_gstin != user_gstin:
            continue  # Skip invoices where user is not the seller
            
        for item in invoice.get("items", []):
            hsn_code = item.get("hsn_code", "")
            
            hsn_entry = {
                "hsn_code": hsn_code,
                "description": item.get("description", ""),
                "uqc": item.get("unit", ""),
                "total_quantity": item.get("quantity", 0),
                "taxable_value": item.get("taxable_value", 0),
                "igst_amount": item.get("igst_amount", 0),
                "cgst_amount": item.get("cgst_amount", 0),
                "sgst_amount": item.get("sgst_amount", 0),
                "cess_amount": item.get("cess_amount", 0),
                "total_value": item.get("taxable_value", 0) + item.get("igst_amount", 0) + 
                             item.get("cgst_amount", 0) + item.get("sgst_amount", 0) + 
                             item.get("cess_amount", 0)
            }
            hsn_items.append(hsn_entry)
    
    return {"items": hsn_items}

def _calculate_overall_summary(self, merged_data: Dict[str, Any], user_gstin: str = None) -> Dict[str, Any]:
    """Calculate overall summary from outward supplies only (invoices where user's GSTIN is the seller)."""
    summary = {
        "total_taxable_value": 0,
        "total_igst": 0,
        "total_cgst": 0,
        "total_sgst": 0,
        "total_cess": 0,
        "total_tax": 0,
        "total_invoice_value": 0,
        "total_invoices": 0
    }
    
    # Sum from B2B supplies (outward supplies only - where user's GSTIN is the seller)
    for invoice in merged_data["gstr1_return"]["b2b_supplies"]["invoices"]:
        # Only include invoices where user is the seller (outward supplies)
        seller_gstin = invoice.get("seller_gstin", "")
        if user_gstin and seller_gstin and seller_gstin != user_gstin:
            continue  # Skip invoices where user is not the seller
            
        summary["total_taxable_value"] += invoice.get("total_taxable_value", 0)
        summary["total_invoice_value"] += invoice.get("invoice_value", 0)
        summary["total_invoices"] += 1
        
        for item in invoice.get("items", []):
            summary["total_igst"] += item.get("igst_amount", 0)
            summary["total_cgst"] += item.get("cgst_amount", 0)
            summary["total_sgst"] += item.get("sgst_amount", 0)
            summary["total_cess"] += item.get("cess_amount", 0)
    
    # Sum from B2CL supplies (outward supplies to large unregistered customers)
    for invoice in merged_data["gstr1_return"]["b2cl_supplies"]["invoices"]:
        # Only include invoices where user is the seller (outward supplies)
        seller_gstin = invoice.get("seller_gstin", "")
        if user_gstin and seller_gstin and seller_gstin != user_gstin:
            continue  # Skip invoices where user is not the seller
            
        summary["total_taxable_value"] += invoice.get("total_taxable_value", 0)
        summary["total_invoice_value"] += invoice.get("invoice_value", 0)
        summary["total_invoices"] += 1
        
        for item in invoice.get("items", []):
            summary["total_igst"] += item.get("igst_amount", 0)
            summary["total_cgst"] += item.get("cgst_amount", 0)
            summary["total_sgst"] += item.get("sgst_amount", 0)
            summary["total_cess"] += item.get("cess_amount", 0)
    
    # Sum from B2CS supplies (outward supplies to small unregistered customers)
    for item in merged_data["gstr1_return"]["b2cs_supplies"]["summary"]:
        summary["total_taxable_value"] += item.get("taxable_value", 0)
        summary["total_igst"] += item.get("igst_amount", 0)
        summary["total_cgst"] += item.get("cgst_amount", 0)
        summary["total_sgst"] += item.get("sgst_amount", 0)
        summary["total_cess"] += item.get("cess_amount", 0)
    
    # Sum from Zero-rated supplies (exports - outward supplies)
    for invoice in merged_data["gstr1_return"]["zero_rated_supplies"]["invoices"]:
        # Only include invoices where user is the seller (outward supplies)
        seller_gstin = invoice.get("seller_gstin", "")
        if user_gstin and seller_gstin and seller_gstin != user_gstin:
            continue  # Skip invoices where user is not the seller
            
        summary["total_taxable_value"] += invoice.get("taxable_value", 0)
        summary["total_invoice_value"] += invoice.get("invoice_value", 0)
        summary["total_invoices"] += 1
    
    # Calculate total tax
    summary["total_tax"] = (summary["total_igst"] + summary["total_cgst"] + 
                          summary["total_sgst"] + summary["total_cess"])
    
    return summary

    async def process_chunks_for_gstr1(self, chunk_contents: List[str], user_gstin: str = None) -> Dict[str, Any]:
        """Process multiple document chunks and merge results into a consolidated GSTR-1 return."""
        gstr1_results = []
        
        for content in chunk_contents:
            result = await self.process_chunk_for_gstr1(content)
            if result:
                gstr1_results.append(result)
        
        # Merge all results using local computation (no Groq)
        return self.merge_gstr1_data(gstr1_results, user_gstin)
