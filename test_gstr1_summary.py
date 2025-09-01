#!/usr/bin/env python3
"""Test script to verify GSTR-1 summary calculations with structured JSON data."""

import sys
import os
sys.path.append('/home/lijo/Documents/finora/server')

from src.gstr1_processor import GSTR1Processor

# Test data with structured JSON matching the schema
test_data = {
    "gstr1_return": {
        "header": {
            "gstin": "27AABCU9603R1ZX",
            "return_period": "032024",
            "filing_date": "2024-04-20",
            "legal_name": "Test Company Ltd",
            "trade_name": "Test Co"
        },
        "b2b_supplies": {
            "invoices": [
                {
                    "invoice_number": "INV001",
                    "invoice_date": "2024-03-15",
                    "seller_gstin": "27AABCU9603R1ZX",  # User's GSTIN - should be included
                    "customer_gstin": "29AABCU9603R1ZY",
                    "customer_name": "Customer A",
                    "place_of_supply": "Karnataka",
                    "reverse_charge": False,
                    "invoice_type": "Regular",
                    "items": [
                        {
                            "description": "Product A",
                            "hsn_code": "1001",
                            "quantity": 10,
                            "unit": "PCS",
                            "rate": 100,
                            "taxable_value": 1000,
                            "igst_rate": 18,
                            "igst_amount": 180,
                            "cgst_rate": 0,
                            "cgst_amount": 0,
                            "sgst_rate": 0,
                            "sgst_amount": 0,
                            "cess_rate": 0,
                            "cess_amount": 0
                        }
                    ],
                    "total_taxable_value": 1000,
                    "total_igst": 180,
                    "total_cgst": 0,
                    "total_sgst": 0,
                    "total_cess": 0,
                    "invoice_value": 1180
                },
                {
                    "invoice_number": "INV002",
                    "invoice_date": "2024-03-16",
                    "seller_gstin": "29AABCU9603R1ZY",  # Different GSTIN - should be excluded
                    "customer_gstin": "27AABCU9603R1ZX",
                    "customer_name": "Test Company Ltd",
                    "place_of_supply": "Karnataka",
                    "reverse_charge": False,
                    "invoice_type": "Regular",
                    "items": [
                        {
                            "description": "Product B",
                            "hsn_code": "2002",
                            "quantity": 5,
                            "unit": "PCS",
                            "rate": 200,
                            "taxable_value": 1000,
                            "igst_rate": 18,
                            "igst_amount": 180,
                            "cgst_rate": 0,
                            "cgst_amount": 0,
                            "sgst_rate": 0,
                            "sgst_amount": 0,
                            "cess_rate": 0,
                            "cess_amount": 0
                        }
                    ],
                    "total_taxable_value": 1000,
                    "total_igst": 180,
                    "total_cgst": 0,
                    "total_sgst": 0,
                    "total_cess": 0,
                    "invoice_value": 1180
                },
                {
                    "invoice_number": "INV003",
                    "invoice_date": "2024-03-17",
                    "seller_gstin": "27AABCU9603R1ZX",  # User's GSTIN - should be included
                    "customer_gstin": "30AABCU9603R1ZZ",
                    "customer_name": "Customer C",
                    "place_of_supply": "Karnataka",
                    "reverse_charge": False,
                    "invoice_type": "Regular",
                    "items": [
                        {
                            "description": "Product C",
                            "hsn_code": "3003",
                            "quantity": 2,
                            "unit": "PCS",
                            "rate": 500,
                            "taxable_value": 1000,
                            "igst_rate": 0,
                            "igst_amount": 0,
                            "cgst_rate": 9,
                            "cgst_amount": 90,
                            "sgst_rate": 9,
                            "sgst_amount": 90,
                            "cess_rate": 0,
                            "cess_amount": 0
                        }
                    ],
                    "total_taxable_value": 1000,
                    "total_igst": 0,
                    "total_cgst": 90,
                    "total_sgst": 90,
                    "total_cess": 0,
                    "invoice_value": 1180
                }
            ]
        },
        "b2cl_supplies": {"invoices": []},
        "b2cs_supplies": {"summary": []},
        "zero_rated_supplies": {"invoices": []},
        "nil_exempt_supplies": {"summary": []},
        "credit_debit_notes": {"notes": []},
        "amendments": {"details": []},
        "documents_issued": {"summary": []},
        "hsn_summary": {"items": []},
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

def test_summary_calculations():
    """Test HSN and overall summary calculations."""
    processor = GSTR1Processor()
    user_gstin = "27AABCU9603R1ZX"
    
    print("=== Testing GSTR-1 Summary Calculations ===")
    print(f"User GSTIN: {user_gstin}")
    print(f"Total invoices in test data: {len(test_data['gstr1_return']['b2b_supplies']['invoices'])}")
    
    # Test HSN summary calculation
    print("\n--- Testing HSN Summary ---")
    hsn_summary = processor._calculate_hsn_summary(test_data, user_gstin)
    print(f"HSN items found: {len(hsn_summary['items'])}")
    
    for item in hsn_summary['items']:
        print(f"HSN: {item['hsn_code']}, Description: {item['description']}, "
              f"Taxable Value: {item['taxable_value']}, Total Value: {item['total_value']}")
    
    # Test overall summary calculation
    print("\n--- Testing Overall Summary ---")
    overall_summary = processor._calculate_overall_summary(test_data, user_gstin)
    
    print("Overall Summary Results:")
    for key, value in overall_summary.items():
        print(f"  {key}: {value}")
    
    # Expected results (only INV001 and INV003 should be included - where user is seller)
    expected_taxable_value = 2000  # 1000 + 1000
    expected_igst = 180  # Only from INV001
    expected_cgst = 90   # Only from INV003
    expected_sgst = 90   # Only from INV003
    expected_total_tax = 360  # 180 + 90 + 90
    expected_invoice_value = 2360  # 1180 + 1180
    expected_invoices = 2  # INV001 and INV003
    
    print(f"\n--- Validation ---")
    print(f"Expected taxable value: {expected_taxable_value}, Actual: {overall_summary['total_taxable_value']}")
    print(f"Expected IGST: {expected_igst}, Actual: {overall_summary['total_igst']}")
    print(f"Expected CGST: {expected_cgst}, Actual: {overall_summary['total_cgst']}")
    print(f"Expected SGST: {expected_sgst}, Actual: {overall_summary['total_sgst']}")
    print(f"Expected total tax: {expected_total_tax}, Actual: {overall_summary['total_tax']}")
    print(f"Expected invoice value: {expected_invoice_value}, Actual: {overall_summary['total_invoice_value']}")
    print(f"Expected invoices: {expected_invoices}, Actual: {overall_summary['total_invoices']}")
    
    # Validation
    success = True
    if overall_summary['total_taxable_value'] != expected_taxable_value:
        print("❌ Taxable value mismatch!")
        success = False
    if overall_summary['total_igst'] != expected_igst:
        print("❌ IGST mismatch!")
        success = False
    if overall_summary['total_cgst'] != expected_cgst:
        print("❌ CGST mismatch!")
        success = False
    if overall_summary['total_sgst'] != expected_sgst:
        print("❌ SGST mismatch!")
        success = False
    if overall_summary['total_tax'] != expected_total_tax:
        print("❌ Total tax mismatch!")
        success = False
    if overall_summary['total_invoice_value'] != expected_invoice_value:
        print("❌ Invoice value mismatch!")
        success = False
    if overall_summary['total_invoices'] != expected_invoices:
        print("❌ Invoice count mismatch!")
        success = False
    
    if success:
        print("✅ All validations passed! Summary calculations are working correctly.")
    else:
        print("❌ Some validations failed. Please check the calculation logic.")
    
    return success

if __name__ == "__main__":
    test_summary_calculations()
