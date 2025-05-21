"""
Cloud Detection Tester

This script directly tests the cloud browser detection functionality
without the complexity of the main application.
"""
import sys
import logging
from cloud_browser_automation import check_for_product_tables_cloud

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_url(url, timeout=20):
    """
    Test cloud detection for a single URL.
    
    Args:
        url: The URL to test
        timeout: Timeout in seconds
        
    Returns:
        dict: Detection result
    """
    logger.info(f"Testing cloud detection for URL: {url} (timeout: {timeout}s)")
    
    try:
        # Call cloud browser detection function directly
        result = check_for_product_tables_cloud(url, timeout)
        logger.info(f"Result for {url}: {result}")
        return result
    except Exception as e:
        logger.error(f"Error processing {url}: {str(e)}")
        return {
            "found": None,
            "class_name": None,
            "detection_method": "error",
            "message": f"Error during detection: {str(e)}"
        }

def main():
    """Main function to test cloud detection with command line arguments."""
    # Use command line argument or default to partly-products test URL
    url = sys.argv[1] if len(sys.argv) > 1 else "https://partly-products-showcase.lovable.app/products"
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 20
    
    logger.info("="*80)
    logger.info(f"CLOUD DETECTION TEST - URL: {url} - TIMEOUT: {timeout}s")
    logger.info("="*80)
    
    result = test_url(url, timeout)
    
    logger.info("="*80)
    logger.info("DETECTION RESULT:")
    logger.info(f"Found: {result.get('found')}")
    logger.info(f"Class Name: {result.get('class_name')}")
    logger.info(f"Detection Method: {result.get('detection_method')}")
    logger.info(f"Message: {result.get('message')}")
    logger.info("="*80)
    
    return result

if __name__ == "__main__":
    main()