#!/usr/bin/env python
"""
Email QA API Testing Script

This script tests the API endpoints directly by making HTTP requests.
"""

import json
import requests
import time

def print_section(title):
    """Print a section title with separators."""
    print("\n" + "="*50)
    print(f" {title} ".center(50, "="))
    print("="*50 + "\n")

def print_result(result_name, data):
    """Pretty print a result section."""
    print(f"\n--- {result_name} ---")
    print(json.dumps(data, indent=2) if isinstance(data, (dict, list)) else data)

def test_basic_qa():
    """Test the basic /run-qa endpoint."""
    print_section("TESTING BASIC QA ENDPOINT")
    
    try:
        # Create test files to upload
        files = {
            'email': ('test_email.html', open('test_files/test_email.html', 'rb')),
            'requirements': ('test_requirements.json', open('test_files/test_requirements.json', 'rb'))
        }
        
        print("Sending API request to /run-qa")
        response = requests.post('http://localhost:5000/run-qa', files=files)
        
        if response.status_code == 200:
            print("✅ API call successful!")
            results = response.json()
            print_result("Metadata Results", results.get('metadata', []))
            print_result("Links Results", results.get('links', []))
        else:
            print(f"❌ API call failed with status code: {response.status_code}")
            print_result("Response", response.text)
    
    except Exception as e:
        print(f"❌ Error during API test: {str(e)}")
        
def test_batch_qa():
    """Test the batch QA endpoint."""
    print_section("TESTING BATCH QA ENDPOINT")
    
    try:
        # Create test files to upload - format correctly for multiple file uploads
        files = [
            ('emails', ('email1.html', open('test_files/test_email.html', 'rb'))),
            ('emails', ('email2.html', open('test_files/localized_email.html', 'rb'))),
            ('requirements', ('test_requirements.json', open('test_files/test_requirements.json', 'rb')))
        ]
        
        print("Sending API request to /run-batch-qa")
        response = requests.post('http://localhost:5000/run-batch-qa', files=files)
        
        if response.status_code == 200:
            print("✅ API call successful!")
            results = response.json()
            print(f"Number of processed emails: {len(results)}")
            for filename, result in results.items():
                print(f"\nResults for {filename}:")
                print_result("Metadata Count", len(result.get('metadata', [])))
                print_result("Links Count", len(result.get('links', [])))
        else:
            print(f"❌ API call failed with status code: {response.status_code}")
            print_result("Response", response.text)
    
    except Exception as e:
        print(f"❌ Error during API test: {str(e)}")

def test_localized_qa():
    """Test the localized QA endpoint."""
    print_section("TESTING LOCALIZED QA ENDPOINT")
    
    try:
        # Create test files to upload
        files = {
            'localized_email': ('localized_email.html', open('test_files/localized_email.html', 'rb')),
            'localized_requirements': ('localized_requirements.json', open('test_files/localized_requirements.json', 'rb')),
            'parent_email': ('parent_email.html', open('test_files/test_email.html', 'rb')),
            'parent_requirements': ('parent_requirements.json', open('test_files/test_requirements.json', 'rb'))
        }
        
        print("Sending API request to /run-localized-qa")
        data = {'compare_to_parent': 'true'}
        response = requests.post('http://localhost:5000/run-localized-qa', files=files, data=data)
        
        if response.status_code == 200:
            print("✅ API call successful!")
            results = response.json()
            print_result("Metadata Results", results.get('metadata', []))
            print_result("Links Count", len(results.get('links', [])))
            print_result("Locale Comparison Count", len(results.get('locale_comparison', [])))
            
            # Check if parent requirements validation is included
            if 'parent_requirements_validation' in results:
                print("✅ Parent requirements validation present")
            else:
                print("❌ Parent requirements validation missing")
        else:
            print(f"❌ API call failed with status code: {response.status_code}")
            print_result("Response", response.text)
    
    except Exception as e:
        print(f"❌ Error during API test: {str(e)}")

if __name__ == "__main__":
    print_section("EMAIL QA API TEST SCRIPT")
    print("This script tests the API endpoints for the Email QA automation tool")
    print("Ensure the server is running on http://localhost:5000 before continuing")
    
    # Give server time to start if it's just been launched
    time.sleep(1)
    
    # Run API tests
    test_basic_qa()
    test_batch_qa()
    test_localized_qa()
    
    print_section("TESTING COMPLETE")