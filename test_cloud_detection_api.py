"""
Direct test script for cloud browser detection API.
Tests the API endpoint directly to verify it's returning correct results.
"""
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_api_endpoint(url="https://partly-products-showcase.lovable.app/products", timeout=20):
    """Test the cloud detection API endpoint."""
    logger.info(f"Testing API endpoint with URL: {url}, timeout: {timeout}")
    
    # The API endpoint URL
    api_url = "http://localhost:5000/api/check_product_tables"
    
    # Request payload
    payload = {
        "urls": [url],
        "timeout": timeout
    }
    
    try:
        # Send POST request to the API
        response = requests.post(api_url, json=payload)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Parse and print the response
            result = response.json()
            logger.info(f"API Response: {json.dumps(result, indent=2)}")
            
            # Extract the specific result for our URL
            url_result = result.get("results", {}).get(url, {})
            
            # Print a formatted summary
            logger.info("=" * 80)
            logger.info("DETECTION RESULT:")
            logger.info(f"Found: {url_result.get('found')}")
            logger.info(f"Class Name: {url_result.get('class_name')}")
            logger.info(f"Detection Method: {url_result.get('detection_method')}")
            logger.info(f"Message: {url_result.get('message')}")
            logger.info("=" * 80)
            
            return url_result
        else:
            logger.error(f"API request failed with status code: {response.status_code}")
            logger.error(f"Response content: {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error testing API endpoint: {str(e)}")
        return None

if __name__ == "__main__":
    # Test the API endpoint
    test_api_endpoint()