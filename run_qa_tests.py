#!/usr/bin/env python3
"""
Email QA Test Runner

This script provides a command-line interface for testing the Email QA functionality
without requiring a browser or GUI.
"""

import argparse
import json
import os
import requests
import sys
from pprint import pprint

SERVER_URL = "http://localhost:5000"

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f" {text} ".center(60, "-"))
    print("=" * 60 + "\n")

def run_single_email_qa(email_path, requirements_path):
    """
    Run QA on a single email file with the provided requirements.
    
    Args:
        email_path: Path to the email HTML file
        requirements_path: Path to the requirements JSON file
    """
    print_header("RUNNING SINGLE EMAIL QA")
    
    # Ensure files exist
    if not os.path.exists(email_path):
        print(f"Error: Email file not found: {email_path}")
        return
    
    if not os.path.exists(requirements_path):
        print(f"Error: Requirements file not found: {requirements_path}")
        return
    
    # Prepare the request
    url = f"{SERVER_URL}/run-qa"
    files = {
        'email': open(email_path, 'rb'),
        'requirements': open(requirements_path, 'rb')
    }
    
    try:
        print(f"Sending request to {url}")
        print(f"Email: {email_path}")
        print(f"Requirements: {requirements_path}")
        
        response = requests.post(url, files=files)
        response.raise_for_status()
        
        # Print the results
        data = response.json()
        
        print("\n--- Metadata Validation ---")
        for item in data.get('metadata', []):
            status_color = "\033[92m" if item['status'] == 'PASS' else "\033[91m"  # Green for PASS, Red for FAIL
            print(f"{status_color}{item['field']}: {item['status']}\033[0m")
            print(f"  Expected: {item['expected']}")
            print(f"  Actual: {item['actual']}")
            print("")
        
        print("\n--- Link Validation ---")
        for item in data.get('links', []):
            status_color = "\033[92m" if item['status'] == 'PASS' else "\033[91m"
            print(f"{status_color}{item['link_text']}: {item['status']}\033[0m")
            print(f"  URL: {item['url']}")
            if 'final_url' in item:
                print(f"  Final URL: {item['final_url']}")
            if 'utm_issues' in item and item['utm_issues']:
                print(f"  UTM Issues: {', '.join(item['utm_issues'])}")
            print("")
        
        print("\nQA validation completed successfully!")
        
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
    finally:
        # Close open file handles
        for f in files.values():
            f.close()

def run_batch_qa(email_paths, requirements_path):
    """
    Run batch QA on multiple email files with the provided requirements.
    
    Args:
        email_paths: List of paths to email HTML files
        requirements_path: Path to the requirements JSON file
    """
    print_header("RUNNING BATCH EMAIL QA")
    
    # Ensure requirements file exists
    if not os.path.exists(requirements_path):
        print(f"Error: Requirements file not found: {requirements_path}")
        return
    
    # Check if email files exist
    valid_emails = []
    for path in email_paths:
        if os.path.exists(path):
            valid_emails.append(path)
        else:
            print(f"Warning: Email file not found: {path}")
    
    if not valid_emails:
        print("Error: No valid email files to process")
        return
    
    # Prepare the request
    url = f"{SERVER_URL}/run-batch-qa"
    
    files = {'requirements': open(requirements_path, 'rb')}
    
    # Add email files
    for i, path in enumerate(valid_emails):
        files[f'emails'] = open(path, 'rb')
    
    try:
        print(f"Sending batch request to {url}")
        print(f"Emails: {', '.join(valid_emails)}")
        print(f"Requirements: {requirements_path}")
        
        response = requests.post(url, files=files)
        response.raise_for_status()
        
        # Print the results
        data = response.json()
        
        for filename, results in data.items():
            print(f"\n--- Results for {filename} ---")
            
            print("\nMetadata Validation:")
            for item in results.get('metadata', []):
                status_color = "\033[92m" if item['status'] == 'PASS' else "\033[91m"
                print(f"{status_color}{item['field']}: {item['status']}\033[0m")
            
            print("\nLink Validation:")
            for item in results.get('links', []):
                status_color = "\033[92m" if item['status'] == 'PASS' else "\033[91m"
                print(f"{status_color}{item['link_text']}: {item['status']}\033[0m")
            
            print("")
        
        print("\nBatch QA validation completed successfully!")
        
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
    finally:
        # Close open file handles
        for f in files.values():
            f.close()

def run_localization_qa(localized_email_path, localized_requirements_path, 
                      parent_email_path=None, parent_requirements_path=None,
                      compare_to_parent=False):
    """
    Run localization QA on email files.
    
    Args:
        localized_email_path: Path to the localized email HTML file
        localized_requirements_path: Path to the localized requirements JSON file
        parent_email_path: Path to the parent email HTML file (optional)
        parent_requirements_path: Path to the parent requirements JSON file (optional)
        compare_to_parent: Whether to compare to parent email
    """
    print_header("RUNNING LOCALIZATION QA")
    
    # Ensure required files exist
    if not os.path.exists(localized_email_path):
        print(f"Error: Localized email file not found: {localized_email_path}")
        return
    
    if not os.path.exists(localized_requirements_path):
        print(f"Error: Localized requirements file not found: {localized_requirements_path}")
        return
    
    if compare_to_parent:
        if not parent_email_path or not os.path.exists(parent_email_path):
            print(f"Error: Parent email file not found: {parent_email_path}")
            return
        
        if not parent_requirements_path or not os.path.exists(parent_requirements_path):
            print(f"Error: Parent requirements file not found: {parent_requirements_path}")
            return
    
    # Prepare the request
    url = f"{SERVER_URL}/run-localized-qa"
    
    files = {
        'localized_email': open(localized_email_path, 'rb'),
        'localized_requirements': open(localized_requirements_path, 'rb'),
    }
    
    data = {'compare_to_parent': compare_to_parent}
    
    if compare_to_parent:
        files['parent_email'] = open(parent_email_path, 'rb')
        files['parent_requirements'] = open(parent_requirements_path, 'rb')
    
    try:
        print(f"Sending localization request to {url}")
        print(f"Localized Email: {localized_email_path}")
        print(f"Localized Requirements: {localized_requirements_path}")
        
        if compare_to_parent:
            print(f"Parent Email: {parent_email_path}")
            print(f"Parent Requirements: {parent_requirements_path}")
            print("Comparing to parent: Yes")
        else:
            print("Comparing to parent: No")
        
        response = requests.post(url, files=files, data=data)
        response.raise_for_status()
        
        # Print the results
        results = response.json()
        
        print("\n--- Localized Metadata Validation ---")
        for item in results.get('metadata', []):
            status_color = "\033[92m" if item['status'] == 'PASS' else "\033[91m"
            print(f"{status_color}{item['field']}: {item['status']}\033[0m")
            print(f"  Expected: {item['expected']}")
            print(f"  Actual: {item['actual']}")
        
        print("\n--- Localized Link Validation ---")
        for item in results.get('links', []):
            status_color = "\033[92m" if item['status'] == 'PASS' else "\033[91m"
            print(f"{status_color}{item['link_text']}: {item['status']}\033[0m")
            print(f"  URL: {item['url']}")
        
        if 'comparison_results' in results:
            print("\n--- Localization Pattern Comparison ---")
            for pattern, result in results['comparison_results'].items():
                status_color = "\033[92m" if result['status'] == 'PASS' else "\033[91m"
                print(f"{status_color}{pattern}: {result['status']}\033[0m")
                if 'details' in result and result['details']:
                    print(f"  Details: {', '.join(result['details'])}")
        
        if 'parent_requirements_validation' in results:
            print("\n--- Validation Against Parent Requirements ---")
            print("\nMetadata:")
            for item in results['parent_requirements_validation']['metadata']:
                status_color = "\033[92m" if item['status'] == 'PASS' else "\033[91m"
                print(f"{status_color}{item['field']}: {item['status']}\033[0m")
            
            print("\nLinks:")
            for item in results['parent_requirements_validation']['links']:
                status_color = "\033[92m" if item['status'] == 'PASS' else "\033[91m"
                print(f"{status_color}{item['link_text']}: {item['status']}\033[0m")
        
        print("\nLocalization QA validation completed successfully!")
        
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
    finally:
        # Close open file handles
        for f in files.values():
            f.close()

def check_server():
    """Check if the server is running."""
    try:
        response = requests.get(f"{SERVER_URL}/")
        if response.status_code == 200:
            print("✅ Server is running and accessible!")
            return True
        else:
            print(f"❌ Server returned unexpected status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to the server. Make sure it's running.")
        return False

def main():
    parser = argparse.ArgumentParser(description='Email QA Testing Tool')
    
    # Add server check command
    parser.add_argument('--check-server', action='store_true',
                        help='Check if the server is running')
    
    # Add subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Single email QA command
    single_parser = subparsers.add_parser('single', help='Run QA on a single email')
    single_parser.add_argument('--email', required=True, help='Path to the email HTML file')
    single_parser.add_argument('--requirements', required=True, help='Path to the requirements JSON file')
    
    # Batch QA command
    batch_parser = subparsers.add_parser('batch', help='Run QA on multiple emails')
    batch_parser.add_argument('--emails', required=True, nargs='+', help='Paths to email HTML files')
    batch_parser.add_argument('--requirements', required=True, help='Path to the requirements JSON file')
    
    # Localization QA command
    locale_parser = subparsers.add_parser('localize', help='Run localization QA')
    locale_parser.add_argument('--localized-email', required=True, help='Path to the localized email HTML file')
    locale_parser.add_argument('--localized-requirements', required=True, help='Path to the localized requirements JSON file')
    locale_parser.add_argument('--parent-email', help='Path to the parent email HTML file')
    locale_parser.add_argument('--parent-requirements', help='Path to the parent requirements JSON file')
    locale_parser.add_argument('--compare', action='store_true', help='Compare localized email to parent')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Check if server is running first (always do this check)
    if not check_server():
        sys.exit(1)
    
    # If only --check-server was specified, exit after the check
    if args.check_server and not args.command:
        sys.exit(0)
    
    # Execute the appropriate command
    if args.command == 'single':
        run_single_email_qa(args.email, args.requirements)
    elif args.command == 'batch':
        run_batch_qa(args.emails, args.requirements)
    elif args.command == 'localize':
        run_localization_qa(
            args.localized_email,
            args.localized_requirements,
            args.parent_email,
            args.parent_requirements,
            args.compare
        )
    else:
        parser.print_help()

if __name__ == '__main__':
    main()