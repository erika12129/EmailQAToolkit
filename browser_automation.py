"""
Browser automation module for Email QA System.
Optimized for cloud environments where browser automation is not available.
This version DOES NOT use Playwright or other browser automation libraries.
"""

import logging
import os
from urllib.parse import urlparse
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_for_product_tables_sync(url: str, timeout: Optional[int] = None) -> Dict[str, Any]:
    """
    Synchronous function that checks for cloud browser availability first,
    and tries to use that before falling back to the standard unavailability message.
    
    Args:
        url: The URL to check for product tables
        timeout: Timeout in seconds (used for cloud browser)
        
    Returns:
        dict: Detection results with standardized message
    """
    # Parse domain to check if it's a test domain
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    is_test_domain = False
    
    # Handle test domains
    try:
        from runtime_config import config
        if config.mode == 'development' and (
            'partly-products-showcase.lovable.app' in domain or 
            'localhost:5001' in domain or 
            '127.0.0.1:5001' in domain
        ):
            is_test_domain = True
    except ImportError:
        # If runtime_config isn't available
        pass
    
    # Check if we're in Replit environment or in a deployed environment
    is_replit = os.environ.get('REPL_ID') is not None or os.environ.get('REPLIT_ENVIRONMENT') is not None
    
    # CRITICAL CHANGE: Check for cloud browser availability
    scrapingbee_key = os.environ.get('SCRAPINGBEE_API_KEY', '')
    browserless_key = os.environ.get('BROWSERLESS_API_KEY', '')
    cloud_browser_available = bool(scrapingbee_key or browserless_key)
    
    # Log available API keys (partial)
    if scrapingbee_key:
        logger.info(f"ScrapingBee API key found: {scrapingbee_key[:4]}...")
    if browserless_key:
        logger.info(f"Browserless API key found: {browserless_key[:4]}...")
    
    # If cloud browser is available, try to use it
    if cloud_browser_available:
        logger.info(f"Cloud browser available - attempting to use for URL: {url}")
        try:
            # Import directly to avoid circular imports
            from cloud_browser_automation import check_for_product_tables_cloud
            return check_for_product_tables_cloud(url, timeout)
        except Exception as e:
            logger.error(f"Cloud browser attempt failed: {str(e)}")
            # Continue to fallback message below
    
    # Standard unavailability messages if cloud browser is not available or failed
    if is_replit:
        logger.info(f"Running in Replit with no cloud browser - automation unavailable for URL: {url}")
        message = 'Unknown - Browser automation unavailable in Replit - manual verification required'
    else:
        logger.warning(f"Browser automation expected but failed in deployment environment for URL: {url}")
        message = 'Error - Browser automation failed in deployment - check server configuration'
    
    # Return standardized message about unavailability
    return {
        'found': None,  # Use None to indicate unknown status
        'class_name': None,
        'error': 'No compatible browsers available',
        'detection_method': 'browser_unavailable',
        'message': message,
        'is_test_domain': is_test_domain
    }