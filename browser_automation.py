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
    Synchronous function that returns a standardized message about browser automation
    being unavailable in cloud environments.
    
    Args:
        url: The URL to check for product tables
        timeout: Timeout in seconds (ignored)
        
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
    
    if is_replit:
        logger.info(f"Running in Replit - browser automation unavailable for URL: {url}")
        message = 'Unknown - Browser automation unavailable in Replit - manual verification required'
    else:
        logger.warning(f"Browser automation expected but failed in deployment environment for URL: {url}")
        message = 'Error - Browser automation failed in deployment - check server configuration'
    
    # Return standardized message about unavailability
    return {
        'found': None,  # Use None to indicate unknown status
        'class_name': None,
        'detection_method': 'browser_unavailable',
        'message': message,
        'is_test_domain': is_test_domain
    }