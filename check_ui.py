import requests
import json
import sys
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def check_product_table_ui():
    """Test that the product table information appears in the UI HTML."""
    try:
        email_path = Path("attached_assets/Replit_test_email.html")
        req_path = Path("attached_assets/sample_requirements.json")
        
        if not email_path.exists() or not req_path.exists():
            logger.error(f"Test files not found: {email_path} or {req_path}")
            return False
        
        # Make the API call
        url = "http://localhost:5000/run-qa"
        files = {
            'email': (email_path.name, open(email_path, 'rb'), 'text/html'),
            'requirements': (req_path.name, open(req_path, 'rb'), 'application/json')
        }
        
        logger.info(f"Making request to {url}")
        response = requests.post(url, files=files)
        
        if response.status_code != 200:
            logger.error(f"API call failed with status code {response.status_code}")
            return False
        
        # Check that product table data exists in the response
        data = response.json()
        product_links = [link for link in data['links'] if link.get('has_product_table')]
        
        if not product_links:
            logger.error("No links with product tables found in API response")
            return False
        
        logger.info(f"Found {len(product_links)} links with product tables")
        for link in product_links[:3]:  # Just log a few for brevity
            logger.info(f"Link {link['url']} has product table: {link['has_product_table']}, class: {link['product_table_class']}")
        
        # Now request the frontend HTML
        html_response = requests.get("http://localhost:5000/")
        
        if html_response.status_code != 200:
            logger.error(f"Failed to get frontend HTML, status code {html_response.status_code}")
            return False
        
        # Check if our product table column appears in the HTML
        html = html_response.text
        if "Product Table Detection" not in html:
            logger.error("Product Table Detection column header not found in HTML")
            return False
        
        logger.info("Product Table Detection column header found in HTML")
        
        # Just to demonstrate it's working, we'll log the result
        logger.info("UI check complete: Product table detection should appear in the UI")
        return True
    
    except Exception as e:
        logger.error(f"Error testing product table UI: {e}")
        return False

if __name__ == "__main__":
    success = check_product_table_ui()
    sys.exit(0 if success else 1)