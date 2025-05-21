"""
Simplified cloud detection demo for product tables.
This script directly demonstrates the core functionality without any of the 
complex routing or special cases in the main application.
"""
import os
import json
import logging
from cloud_browser_automation import check_for_product_tables_cloud

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def demo_product_table_detection(url):
    """
    Demonstrate the direct cloud detection of product tables in a URL.
    This is the simplest possible demo of the core functionality.
    
    Args:
        url: The URL to check for product tables
        
    Returns:
        dict: Detection results
    """
    logger.info(f"Testing cloud detection for URL: {url}")
    
    try:
        # Call cloud detection directly
        result = check_for_product_tables_cloud(url, timeout=20)
        
        # Print a summary of the results
        logger.info("=" * 80)
        logger.info("DETECTION RESULTS:")
        logger.info(f"Found: {result.get('found')}")
        logger.info(f"Class Name: {result.get('class_name')}")
        logger.info(f"Detection Method: {result.get('detection_method')}")
        logger.info(f"Message: {result.get('message')}")
        logger.info("=" * 80)
        
        # Pretty print the full results
        logger.info(f"Full results: {json.dumps(result, indent=2)}")
        
        return result
    except Exception as e:
        logger.error(f"Error during detection: {str(e)}")
        return {
            "found": None,
            "class_name": None,
            "detection_method": "error",
            "message": f"Error: {str(e)}"
        }

if __name__ == "__main__":
    # Test URL with known product tables
    test_url = "https://partly-products-showcase.lovable.app/products"
    
    # Run the demo
    demo_product_table_detection(test_url)