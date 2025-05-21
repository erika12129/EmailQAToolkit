"""
Direct testing script for cloud browser detection.
Tests the cloud detection directly without going through API endpoints.
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_direct_cloud_detection(url: str, timeout: int = 20) -> Dict[str, Any]:
    """
    Directly test the cloud browser detection for product tables.
    
    Args:
        url: The URL to check
        timeout: Timeout in seconds
        
    Returns:
        dict: Detection results
    """
    try:
        # Import the cloud browser function directly
        from cloud_browser_automation import check_for_product_tables_cloud
        
        # Call the cloud browser detection
        logger.info(f"Calling check_for_product_tables_cloud for URL: {url}")
        start_time = time.time()
        result = check_for_product_tables_cloud(url, timeout)
        duration = time.time() - start_time
        
        # Log the result for debugging
        logger.info(f"Detection completed in {duration:.2f}s")
        logger.info(f"Result: {json.dumps(result, indent=2)}")
        
        return result
    except Exception as e:
        logger.error(f"Error during direct cloud detection: {str(e)}")
        logger.exception("Full traceback:")
        return {
            "error": str(e),
            "success": False
        }

def main():
    """Main function."""
    # URL to test
    url = "https://partly-products-showcase.lovable.app/products"
    
    # Test the direct cloud detection
    logger.info(f"Testing direct cloud detection for URL: {url}")
    result = test_direct_cloud_detection(url)
    
    # Format and print the result
    logger.info("Detection complete!")
    logger.info(f"Found: {result.get('found')}")
    logger.info(f"Class name: {result.get('class_name')}")
    logger.info(f"Detection method: {result.get('detection_method')}")
    logger.info(f"Message: {result.get('message')}")
    
    # Check if the detection was successful
    if result.get('found') is True:
        logger.info("✅ SUCCESS: Product table detected!")
    else:
        logger.info("❌ FAILURE: Product table not detected or detection error")
        if result.get('error'):
            logger.error(f"Error: {result.get('error')}")

if __name__ == "__main__":
    main()