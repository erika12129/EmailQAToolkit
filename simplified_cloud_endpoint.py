"""
Simplified cloud detection endpoint for main application.
This file will be imported into main.py to replace the complex detection logic.
"""
import logging
from typing import Dict, Any, List, Optional
from cloud_browser_automation import check_for_product_tables_cloud
import json

# Configure logging
logger = logging.getLogger(__name__)

def check_product_tables_endpoint(urls: List[str], timeout: Optional[int] = None) -> Dict[str, Any]:
    """
    Check if the specified URLs contain product tables using cloud detection.
    Completely reimplemented to directly use cloud detection and preserve all results.
    
    Args:
        urls: List of URLs to check for product tables
        timeout: Timeout for each check in seconds
        
    Returns:
        dict: Results of product table detection for each URL
    """
    # Set default timeout if not provided
    if timeout is None:
        timeout = 20
        
    logger.info(f"FIXED ENDPOINT: Processing {len(urls)} URLs with direct cloud detection (timeout: {timeout}s)")
    
    # Initialize results dictionary
    results = {}
    
    # Process each URL with direct cloud detection
    for url in urls:
        logger.info(f"FIXED ENDPOINT: Processing URL {url} with timeout {timeout}s")
        
        try:
            # Direct call to cloud detection function - NO SPECIAL HANDLING
            cloud_result = check_for_product_tables_cloud(url, timeout)
            
            # Debug print the result
            logger.info(f"Cloud detection raw result: {json.dumps(cloud_result)}")
            
            # Simply use the exact result from cloud detection without modifying it
            results[url] = cloud_result
            
            # Log success with detailed information
            logger.info(f"FIXED ENDPOINT: Successfully detected for {url}: found={cloud_result.get('found')}, class={cloud_result.get('class_name')}")
        except Exception as e:
            logger.error(f"FIXED ENDPOINT: Error processing {url}: {str(e)}")
            # Provide a clear error message for failures
            results[url] = {
                "found": None,
                "class_name": None,
                "detection_method": "error",
                "message": f"Error during detection: {str(e)}",
                "is_test_domain": False
            }
    
    # Return results wrapped for frontend with critical logging
    logger.info(f"FIXED ENDPOINT: Final results: {json.dumps({'results': results})}")
    return {"results": results}