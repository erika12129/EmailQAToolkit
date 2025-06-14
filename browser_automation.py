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
    
    # FIXED: We no longer use special case handling for test domains
    # Instead, we'll rely on the actual cloud detection results for all domains
    logger.info(f"IMPROVED: Using actual detection for domain: {domain}")
    
    # Check if test domain (for logging purposes only)
    if domain == 'example.com' or 'partly-products-showcase.lovable.app' in domain:
        logger.info(f"TEST DOMAIN: {domain} - Using real cloud detection (not special case)")
    
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
            
            # Ensure environment variables are available
            if scrapingbee_key:
                os.environ['SCRAPINGBEE_API_KEY'] = scrapingbee_key
                logger.info(f"Set ScrapingBee API key in environment: {scrapingbee_key[:4]}...")
            if browserless_key:
                os.environ['BROWSERLESS_API_KEY'] = browserless_key
                logger.info(f"Set Browserless API key in environment: {browserless_key[:4]}...")
                
            # Direct call to cloud API function with enhanced logging
            logger.info(f"Making DIRECT cloud API call for {url} with timeout {timeout}")
            result = check_for_product_tables_cloud(url, timeout)
            
            # Check for specific error patterns
            if result.get('error') and isinstance(result['error'], str):
                error_text = result['error'].lower()
                if 'api key' in error_text and ('invalid' in error_text or 'unauthorized' in error_text):
                    logger.error(f"Invalid or unauthorized API key detected: {result['error']}")
                    result['message'] = "Cloud browser error: API key is invalid or unauthorized"
                elif 'timeout' in error_text:
                    logger.warning(f"Timeout detected in cloud browser response: {result['error']}")
                    result['message'] = "Cloud browser timed out while processing the request"
            
            logger.info(f"DIRECT cloud API result for {url}: {result}")
            
            # Add a marker to indicate this came from cloud browser
            result['cloud_browser_used'] = True
            return result
            
        except ImportError as ie:
            logger.error(f"Failed to import cloud_browser_automation module: {str(ie)}")
            return {
                'found': None,
                'class_name': None,
                'detection_method': 'cloud_browser_import_error',
                'message': f'Cloud browser module not available: {str(ie)}',
                'cloud_browser_error': True
            }
        except Exception as e:
            logger.error(f"Cloud browser attempt failed: {str(e)}")
            logger.exception("Full exception for cloud browser failure:")
            
            # Provide more context about the error
            error_context = str(e)
            if 'ConnectionError' in error_context or 'ConnectionRefused' in error_context:
                error_message = 'Network connection error accessing cloud browser API'
            elif 'Timeout' in error_context:
                error_message = 'Cloud browser API request timed out'
            elif 'JSON' in error_context:
                error_message = 'Error parsing cloud browser API response'
            else:
                error_message = f'Cloud browser error: {str(e)}'
                
            return {
                'found': None,
                'class_name': None,
                'detection_method': 'cloud_browser_error',
                'message': error_message,
                'error': str(e),
                'cloud_browser_error': True
            }
            # If we return here, we don't continue to fallback below
    
    # Standard unavailability messages if cloud browser is not available or failed
    # We should ALWAYS return "Unknown" status if browser automation is unavailable
    # This is to ensure users manually check and don't rely on URL patterns
    
    # Never use URL patterns to determine if something is a product page
    # Always return "Unknown" status if we can't verify with browser automation
    logger.info(f"Browser automation unavailable, returning 'Unknown' status requiring manual check: {url}")
    message = 'Unknown - manual verification required'
    found_status = None  # NULL indicates "Unknown" status
    
    # Return standardized message about unavailability with appropriate found status
    return {
        'found': found_status,
        'class_name': None,
        'error': 'No compatible browsers available',
        'detection_method': 'browser_unavailable',
        'message': message,
        'is_test_domain': is_test_domain
    }