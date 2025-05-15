"""
Cloud-based browser automation for Email QA System.
Uses external browser automation APIs to check for product tables without requiring
local browser installation.
"""

import os
import logging
import json
import time
from urllib.parse import urlparse, quote
import requests
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
SCRAPINGBEE_API_KEY = os.environ.get('SCRAPINGBEE_API_KEY', '')
BROWSERLESS_API_KEY = os.environ.get('BROWSERLESS_API_KEY', '')

def check_for_product_tables_cloud(url: str, timeout: Optional[int] = None) -> Dict[str, Any]:
    """
    Check if a URL's HTML contains product table classes using a cloud browser service.
    
    Args:
        url: The URL to check for product tables
        timeout: Timeout in seconds (default: None, uses provider default)
        
    Returns:
        dict: Detection results
    """
    if timeout is None:
        timeout = 30  # Default timeout for cloud services
    
    # Parse domain for logging
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    is_test_domain = False
    
    # Re-check API keys from environment (in case they were set after module was loaded)
    global SCRAPINGBEE_API_KEY, BROWSERLESS_API_KEY
    current_scrapingbee_key = os.environ.get('SCRAPINGBEE_API_KEY', '')
    current_browserless_key = os.environ.get('BROWSERLESS_API_KEY', '')
    
    # Update global variables if environment has newer values
    if current_scrapingbee_key and current_scrapingbee_key != SCRAPINGBEE_API_KEY:
        SCRAPINGBEE_API_KEY = current_scrapingbee_key
        logger.info(f"Updated ScrapingBee API key from environment: {SCRAPINGBEE_API_KEY[:4]}...")
    
    if current_browserless_key and current_browserless_key != BROWSERLESS_API_KEY:
        BROWSERLESS_API_KEY = current_browserless_key
        logger.info(f"Updated Browserless API key from environment: {BROWSERLESS_API_KEY[:4]}...")
    
    # Log the attempt
    logger.info(f"Checking for product tables via cloud service on {domain}")
    
    # Determine which cloud service to use
    if SCRAPINGBEE_API_KEY:
        logger.info(f"Using ScrapingBee API (key: {SCRAPINGBEE_API_KEY[:4]}...) for {domain}")
        return check_with_scrapingbee(url, timeout)
    elif BROWSERLESS_API_KEY:
        logger.info(f"Using Browserless API (key: {BROWSERLESS_API_KEY[:4]}...) for {domain}")
        return check_with_browserless(url, timeout)
    else:
        logger.error("No cloud browser service API key available")
        return {
            'found': None,
            'class_name': None,
            'detection_method': 'cloud_api_not_configured',
            'message': 'Error - Cloud browser service not configured - add API key',
            'is_test_domain': is_test_domain
        }

def check_with_scrapingbee(url: str, timeout: int) -> Dict[str, Any]:
    """
    Check for product tables using ScrapingBee's API.
    
    Args:
        url: The URL to check
        timeout: Timeout in seconds
        
    Returns:
        dict: Detection results
    """
    import base64
    
    # Enforce a safe timeout to prevent indefinite hanging
    if timeout is None or timeout <= 0:
        timeout = 30  # Default 30 seconds
    elif timeout > 60:
        timeout = 60  # Maximum 60 seconds
        
    # Log the actual timeout we're using
    logger.info(f"Using timeout of {timeout} seconds for ScrapingBee request to {url}")
    
    # Re-check API key from environment (in case it was set after module was loaded)
    global SCRAPINGBEE_API_KEY
    current_key = os.environ.get('SCRAPINGBEE_API_KEY', '')
    if current_key and current_key != SCRAPINGBEE_API_KEY:
        SCRAPINGBEE_API_KEY = current_key
        logger.info(f"Updated ScrapingBee API key from environment: {SCRAPINGBEE_API_KEY[:4]}...")
    
    # Check if API key is available
    if not SCRAPINGBEE_API_KEY:
        logger.error("ScrapingBee API key not configured")
        return {
            'found': None,
            'class_name': None,
            'detection_method': 'cloud_api_not_configured',
            'message': 'Error - ScrapingBee API key not configured'
        }
    
    # JavaScript code to execute in the page to find product tables
    js_script = """
    // Function to check if a div has specific class patterns we're looking for
    function checkForProductTables() {
        // Results container
        const results = {
            found: false,
            class_name: null,
            pattern: null,
            definitely_no_products: false
        };
        
        // Check for "noPartsPhrase" class which definitely indicates NO products
        const noProductsElements = document.querySelectorAll('.noPartsPhrase');
        if (noProductsElements.length > 0) {
            results.found = false;
            results.class_name = 'noPartsPhrase';
            results.definitely_no_products = true;
            return results;
        }
        
        // Look for class names starting with "product-table"
        const productTableElements = Array.from(document.querySelectorAll('*[class*="product-table"]'));
        if (productTableElements.length > 0) {
            const element = productTableElements[0];
            results.found = true;
            results.class_name = Array.from(element.classList).find(cls => cls.startsWith('product-table'));
            results.pattern = 'product-table*';
            return results;
        }
        
        // Look for class names ending with "productListContainer"
        const productListElements = Array.from(document.querySelectorAll('*[class*="productListContainer"]'));
        if (productListElements.length > 0) {
            const element = productListElements[0];
            results.found = true;
            results.class_name = Array.from(element.classList).find(cls => cls.endsWith('productListContainer'));
            results.pattern = '*productListContainer';
            return results;
        }
        
        // No matches found
        return results;
    }
    
    // Run the check and return results
    return checkForProductTables();
    """
    
    # Properly encode JavaScript with base64 for ScrapingBee
    import base64
    from urllib.parse import quote_plus
    
    # Ensure proper encoding - first base64 encode the script, then URL encode the base64 string
    encoded_js = base64.b64encode(js_script.encode('utf-8')).decode('utf-8')
    # URL encode the base64 string to ensure special characters are properly handled
    url_encoded_js = quote_plus(encoded_js)
    
    logger.info(f"Using base64 encoded and URL-encoded JS snippet for ScrapingBee API")
    
    # Enforce a reasonable timeout
    if timeout > 30:
        logger.warning(f"Limiting timeout from {timeout}s to 30s to prevent hanging requests")
        timeout = 30
    
    # Construct the API URL with properly encoded parameters and additional parameters for reliability
    api_url = (
        f"https://app.scrapingbee.com/api/v1/?"
        f"api_key={SCRAPINGBEE_API_KEY}&"
        f"url={quote(url)}&"
        f"render_js=true&"
        f"js_snippet={url_encoded_js}&"
        f"timeout={timeout * 1000}&"
        f"premium_proxy=true"
    )
    
    try:
        # Make the request to ScrapingBee with proper timeout handling
        start_time = time.time()
        logger.info(f"Making ScrapingBee API request to {url} (timeout: {timeout}s)")
        
        # Use a slightly larger timeout for the request itself
        request_timeout = min(timeout + 5, 35)  # Never exceed 35 seconds total
        
        # Make the request with detailed logging
        response = requests.get(api_url, timeout=request_timeout)
        duration = time.time() - start_time
        
        logger.info(f"ScrapingBee response received in {duration:.2f}s with status code {response.status_code}")
        logger.info(f"Response content type: {response.headers.get('content-type', 'unknown')}")
        
        # Check for errors in the response
        if response.status_code != 200:
            logger.error(f"ScrapingBee API error: {response.status_code} - {response.text}")
            return {
                'found': None,
                'class_name': None,
                'detection_method': 'cloud_api_error',
                'message': f'Error - ScrapingBee API returned status {response.status_code}',
                'error': response.text
            }
        
        # Parse the response (ScrapingBee returns the JS result as JSON, but might return HTML or other formats on error)
        # Variables to hold response information
        content_type = response.headers.get('content-type', '')
        response_text = response.text.strip()
        
        # Log response details for debugging
        logger.info(f"ScrapingBee response content type: {content_type}")
        logger.info(f"ScrapingBee response starts with: {response_text[:30]}...")
        
        try:
            # Try to parse as JSON
            result = response.json()
            
            # Extract results from the JavaScript execution
            found = result.get('found', False)
            class_name = result.get('class_name')
            pattern = result.get('pattern')
            definitely_no_products = result.get('definitely_no_products', False)
            
            if definitely_no_products:
                logger.info(f"Definitely no products found on {url}: class='{class_name}'")
                return {
                    'found': False,
                    'class_name': class_name,
                    'detection_method': 'cloud_browser_api',
                    'message': f'No products found - detected class: {class_name}'
                }
            elif found and class_name:
                logger.info(f"Product table found on {url}: class='{class_name}', pattern='{pattern}'")
                return {
                    'found': True,
                    'class_name': class_name,
                    'detection_method': 'cloud_browser_api',
                    'message': f'Product table found - class: {class_name}, pattern: {pattern}'
                }
            else:
                logger.info(f"No product table found on {url}")
                return {
                    'found': False,
                    'class_name': None,
                    'detection_method': 'cloud_browser_api',
                    'message': 'No product table found'
                }
                
        except json.JSONDecodeError:
            # Log detailed error information
            logger.error(f"Failed to parse ScrapingBee response as JSON: {response.text[:200]}")
            
            try:
                # Check if we got HTML instead of JSON (common error case)
                if '<html' in response_text.lower() or '<!doctype html' in response_text.lower():
                    logger.error("ScrapingBee returned HTML instead of JSON - likely a JS execution error")
                    return {
                        'found': None,
                        'class_name': None,
                        'detection_method': 'cloud_api_html_response',
                        'message': 'Error - ScrapingBee returned HTML instead of JSON. The JavaScript may have failed to execute.',
                        'content_type': content_type
                    }
                else:
                    # Generic error for other invalid response types
                    return {
                        'found': None,
                        'class_name': None,
                        'detection_method': 'cloud_api_invalid_response',
                        'message': f'Error - Failed to parse ScrapingBee response (content-type: {content_type})',
                        'content_type': content_type
                    }
            except NameError:
                # If response_text or content_type variables are undefined for some reason
                return {
                    'found': None,
                    'class_name': None,
                    'detection_method': 'cloud_api_invalid_response',
                    'message': 'Error - Failed to parse ScrapingBee response',
                    'error_details': 'Variable access error in error handler'
                }
            
    except requests.RequestException as e:
        logger.error(f"ScrapingBee request error: {str(e)}")
        return {
            'found': None,
            'class_name': None,
            'detection_method': 'cloud_api_request_error',
            'message': f'Error - ScrapingBee request failed: {str(e)}'
        }

def check_with_browserless(url: str, timeout: int) -> Dict[str, Any]:
    """
    Check for product tables using Browserless.io's API.
    
    Args:
        url: The URL to check
        timeout: Timeout in seconds
        
    Returns:
        dict: Detection results
    """
    # Re-check API key from environment (in case it was set after module was loaded)
    global BROWSERLESS_API_KEY
    current_key = os.environ.get('BROWSERLESS_API_KEY', '')
    if current_key and current_key != BROWSERLESS_API_KEY:
        BROWSERLESS_API_KEY = current_key
        logger.info(f"Updated Browserless API key from environment: {BROWSERLESS_API_KEY[:4]}...")
    
    # Check if API key is available
    if not BROWSERLESS_API_KEY:
        logger.error("Browserless API key not configured")
        return {
            'found': None,
            'class_name': None,
            'detection_method': 'cloud_api_not_configured',
            'message': 'Error - Browserless API key not configured'
        }
    
    # JavaScript code to execute in the page to find product tables
    js_script = """
    async function checkForProductTables() {
        // Results container
        const results = {
            found: false,
            class_name: null,
            pattern: null,
            definitely_no_products: false
        };
        
        // Check for "noPartsPhrase" class which definitely indicates NO products
        const noProductsElements = document.querySelectorAll('.noPartsPhrase');
        if (noProductsElements.length > 0) {
            results.found = false;
            results.class_name = 'noPartsPhrase';
            results.definitely_no_products = true;
            return results;
        }
        
        // Look for class names starting with "product-table"
        const productTableElements = Array.from(document.querySelectorAll('*[class*="product-table"]'));
        if (productTableElements.length > 0) {
            const element = productTableElements[0];
            results.found = true;
            results.class_name = Array.from(element.classList).find(cls => cls.startsWith('product-table'));
            results.pattern = 'product-table*';
            return results;
        }
        
        // Look for class names ending with "productListContainer"
        const productListElements = Array.from(document.querySelectorAll('*[class*="productListContainer"]'));
        if (productListElements.length > 0) {
            const element = productListElements[0];
            results.found = true;
            results.class_name = Array.from(element.classList).find(cls => cls.endsWith('productListContainer'));
            results.pattern = '*productListContainer';
            return results;
        }
        
        // No matches found
        return results;
    }
    
    // Define the structure of the response
    return await checkForProductTables();
    """
    
    # Construct the API request
    api_url = f"https://chrome.browserless.io/function?token={BROWSERLESS_API_KEY}"
    payload = {
        "code": js_script,
        "context": {
            "url": url,
            "timeout": timeout * 1000,  # Browserless uses milliseconds
            "waitFor": {
                "selectorOrFunctionOrTimeout": 2000  # Wait at least 2 seconds for page to load
            }
        }
    }
    
    try:
        # Make the request to Browserless
        start_time = time.time()
        response = requests.post(api_url, json=payload, timeout=timeout + 5)  # Add buffer to timeout
        duration = time.time() - start_time
        
        logger.info(f"Browserless response received in {duration:.2f}s with status code {response.status_code}")
        
        # Check for errors in the response
        if response.status_code != 200:
            logger.error(f"Browserless API error: {response.status_code} - {response.text}")
            return {
                'found': None,
                'class_name': None,
                'detection_method': 'cloud_api_error',
                'message': f'Error - Browserless API returned status {response.status_code}',
                'error': response.text
            }
        
        # Parse the response as JSON
        try:
            result = response.json()
            
            # Extract results from the JavaScript execution
            found = result.get('found', False)
            class_name = result.get('class_name')
            pattern = result.get('pattern')
            definitely_no_products = result.get('definitely_no_products', False)
            
            if definitely_no_products:
                logger.info(f"Definitely no products found on {url}: class='{class_name}'")
                return {
                    'found': False,
                    'class_name': class_name,
                    'detection_method': 'cloud_browser_api',
                    'message': f'No products found - detected class: {class_name}'
                }
            elif found and class_name:
                logger.info(f"Product table found on {url}: class='{class_name}', pattern='{pattern}'")
                return {
                    'found': True,
                    'class_name': class_name,
                    'detection_method': 'cloud_browser_api',
                    'message': f'Product table found - class: {class_name}, pattern: {pattern}'
                }
            else:
                logger.info(f"No product table found on {url}")
                return {
                    'found': False,
                    'class_name': None,
                    'detection_method': 'cloud_browser_api',
                    'message': 'No product table found'
                }
                
        except json.JSONDecodeError:
            logger.error(f"Failed to parse Browserless response as JSON: {response.text[:200]}")
            return {
                'found': None,
                'class_name': None,
                'detection_method': 'cloud_api_invalid_response',
                'message': 'Error - Failed to parse Browserless response'
            }
            
    except requests.RequestException as e:
        logger.error(f"Browserless request error: {str(e)}")
        return {
            'found': None,
            'class_name': None,
            'detection_method': 'cloud_api_request_error',
            'message': f'Error - Browserless request failed: {str(e)}'
        }