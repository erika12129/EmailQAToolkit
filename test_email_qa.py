#!/usr/bin/env python
"""
Email QA Testing Script

This script demonstrates the core functionality of the Email QA system by:
1. Testing basic email validation
2. Testing batch email processing 
3. Testing localization comparison
"""

import json
import os
from email_qa import validate_email

def print_section(title):
    """Print a section title with separators."""
    print("\n" + "="*50)
    print(f" {title} ".center(50, "="))
    print("="*50 + "\n")

def print_result(result_name, data):
    """Pretty print a result section."""
    print(f"\n--- {result_name} ---")
    print(json.dumps(data, indent=2))

def test_basic_validation():
    """Test basic email validation with a single email."""
    print_section("BASIC EMAIL VALIDATION")
    
    email_path = "static/sample_email.html"
    requirements_path = "static/sample_requirements.json"
    
    print(f"Testing email: {email_path}")
    print(f"Against requirements: {requirements_path}")
    
    results = validate_email(email_path, requirements_path)
    
    print("\nValidation Results:")
    print_result("Metadata", results["metadata"])
    print_result("Links", results["links"])
    
    # Check for pass/fail
    metadata_status = all(item["status"] == "PASS" for item in results["metadata"])
    links_status = all(item["status"] == "PASS" for item in results["links"])
    
    # For localization test, also check locale comparison if it's present
    locale_status = True
    if "locale_comparison" in results:
        locale_status = all(item["status"] == "PASS" for item in results["locale_comparison"])
    
    if metadata_status and links_status and locale_status:
        print("\n✅ All checks passed!")
    else:
        print("\n❌ Some checks failed!")

def test_batch_validation():
    """Test batch validation with multiple emails."""
    print_section("BATCH EMAIL VALIDATION")
    
    emails = [
        "static/sample_email.html", 
        "static/sample_localized_email.html"
    ]
    requirements_path = "static/sample_requirements.json"
    
    print(f"Testing {len(emails)} emails:")
    for email in emails:
        print(f"  - {email}")
    print(f"Against requirements: {requirements_path}")
    
    results = {}
    for email in emails:
        print(f"\nProcessing {os.path.basename(email)}...")
        results[os.path.basename(email)] = validate_email(email, requirements_path)
    
    # Print summary
    print("\nBatch Validation Summary:")
    for filename, result in results.items():
        metadata_status = all(item["status"] == "PASS" for item in result["metadata"])
        links_status = all(item["status"] == "PASS" for item in result["links"])
        overall = "✅ PASS" if metadata_status and links_status else "❌ FAIL"
        print(f"  - {filename}: {overall}")

def test_localization_comparison():
    """Test localization comparison between parent and localized emails."""
    print_section("LOCALIZATION COMPARISON")
    
    parent_email = "static/sample_email.html"
    parent_req = "static/sample_requirements.json"
    
    localized_email = "static/sample_localized_email.html"
    localized_req = "static/sample_localized_requirements.json"
    
    print(f"Testing localized email: {localized_email}")
    print(f"Against localized requirements: {localized_req}")
    print(f"Comparing with parent email: {parent_email}")
    
    # Run validation with comparison to parent
    results = validate_email(
        localized_email, 
        localized_req,
        compare_to_parent=True,
        parent_email_path=parent_email
    )
    
    print("\nLocalization Validation Results:")
    print_result("Metadata", results["metadata"])
    print_result("Links", results["links"])
    
    # If locale_comparison is in results
    if "locale_comparison" in results:
        print_result("Locale Comparison", results["locale_comparison"])
    
    # Check for pass/fail
    metadata_status = all(item["status"] == "PASS" for item in results["metadata"])
    links_status = all(item["status"] == "PASS" for item in results["links"])
    
    # Check localization comparison if present
    locale_status = True
    if "locale_comparison" in results:
        locale_status = all(item["status"] == "PASS" for item in results["locale_comparison"])
        print(f"\nLocalization pattern matching: {'✅ PASS' if locale_status else '❌ FAIL'}")
    
    if metadata_status and links_status and locale_status:
        print("\n✅ Localized email passes all checks!")
    else:
        failed_checks = []
        if not metadata_status: failed_checks.append("metadata")
        if not links_status: failed_checks.append("links")
        if not locale_status: failed_checks.append("localization patterns")
        print(f"\n❌ Some localization checks failed: {', '.join(failed_checks)}")

if __name__ == "__main__":
    print_section("EMAIL QA AUTOMATION TEST SCRIPT")
    print("This script demonstrates the functionality of the Email QA system.")
    
    test_basic_validation()
    test_batch_validation()
    test_localization_comparison()
    
    print_section("TESTING COMPLETE")