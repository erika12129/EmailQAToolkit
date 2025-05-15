"""
Testing module for cloud browser automation API.
This allows users to test if their API key is working.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Union

# Local imports
from cloud_browser_automation import (
    check_with_scrapingbee, 
    check_with_browserless,
    SCRAPINGBEE_API_KEY,
    BROWSERLESS_API_KEY
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_cloud_api(api_key: Optional[str] = None, service: Optional[str] = None) -> Dict[str, Any]:
    """
    Test if a cloud browser API key is working properly.
    
    Args:
        api_key: The API key to test
        service: The service to test ('scrapingbee' or 'browserless')
        
    Returns:
        dict: Test results with status and message
    """
    # Get API keys from arguments or environment
    scrapingbee_key = api_key if service == 'scrapingbee' else SCRAPINGBEE_API_KEY
    browserless_key = api_key if service == 'browserless' else BROWSERLESS_API_KEY
    
    # Determine which service to test
    if service == 'scrapingbee' or (service is None and scrapingbee_key):
        return test_scrapingbee(scrapingbee_key)
    elif service == 'browserless' or (service is None and browserless_key):
        return test_browserless(browserless_key)
    else:
        return {
            'success': False,
            'service': None,
            'message': 'No API key or service specified'
        }

def test_scrapingbee(api_key: Optional[str]) -> Dict[str, Any]:
    """
    Test if a ScrapingBee API key is working.
    
    Args:
        api_key: The ScrapingBee API key to test
        
    Returns:
        dict: Test results
    """
    if not api_key:
        return {
            'success': False,
            'service': 'scrapingbee',
            'message': 'No ScrapingBee API key provided'
        }
    
    # Test URL - use a simple, stable site
    test_url = 'https://example.com'
    
    try:
        # Set API key in environment for the test
        old_key = os.environ.get('SCRAPINGBEE_API_KEY')
        os.environ['SCRAPINGBEE_API_KEY'] = api_key
        
        # Try to fetch a simple site
        logger.info(f"Testing ScrapingBee API key with {test_url}")
        result = check_with_scrapingbee(test_url, 10)
        
        # Restore original key
        if old_key:
            os.environ['SCRAPINGBEE_API_KEY'] = old_key
        else:
            del os.environ['SCRAPINGBEE_API_KEY']
        
        # Check if the request was successful
        if result and ('found' in result or 'error' not in result):
            return {
                'success': True,
                'service': 'scrapingbee',
                'message': 'ScrapingBee API key is working',
                'result': result
            }
        else:
            return {
                'success': False,
                'service': 'scrapingbee',
                'message': f"ScrapingBee API error: {result.get('message', 'Unknown error')}",
                'result': result
            }
    except Exception as e:
        logger.error(f"Error testing ScrapingBee API key: {str(e)}")
        return {
            'success': False,
            'service': 'scrapingbee',
            'message': f"Error testing ScrapingBee API key: {str(e)}"
        }

def test_browserless(api_key: Optional[str]) -> Dict[str, Any]:
    """
    Test if a Browserless API key is working.
    
    Args:
        api_key: The Browserless API key to test
        
    Returns:
        dict: Test results
    """
    if not api_key:
        return {
            'success': False,
            'service': 'browserless',
            'message': 'No Browserless API key provided'
        }
    
    # Test URL - use a simple, stable site
    test_url = 'https://example.com'
    
    try:
        # Set API key in environment for the test
        old_key = os.environ.get('BROWSERLESS_API_KEY')
        os.environ['BROWSERLESS_API_KEY'] = api_key
        
        # Try to fetch a simple site
        logger.info(f"Testing Browserless API key with {test_url}")
        result = check_with_browserless(test_url, 10)
        
        # Restore original key
        if old_key:
            os.environ['BROWSERLESS_API_KEY'] = old_key
        else:
            del os.environ['BROWSERLESS_API_KEY']
        
        # Check if the request was successful
        if result and ('found' in result or 'error' not in result):
            return {
                'success': True,
                'service': 'browserless',
                'message': 'Browserless API key is working',
                'result': result
            }
        else:
            return {
                'success': False,
                'service': 'browserless',
                'message': f"Browserless API error: {result.get('message', 'Unknown error')}",
                'result': result
            }
    except Exception as e:
        logger.error(f"Error testing Browserless API key: {str(e)}")
        return {
            'success': False,
            'service': 'browserless',
            'message': f"Error testing Browserless API key: {str(e)}"
        }

def get_api_status() -> Dict[str, Any]:
    """
    Get the status of configured cloud browser APIs.
    
    Returns:
        dict: Status of cloud browser APIs
    """
    # Check which APIs are configured
    result = {
        'cloud_browser_available': False,
        'services': {}
    }
    
    # Check ScrapingBee
    if SCRAPINGBEE_API_KEY:
        result['services']['scrapingbee'] = {
            'configured': True,
            'key_prefix': SCRAPINGBEE_API_KEY[:4] + '...'  # Show only prefix for security
        }
        result['cloud_browser_available'] = True
    else:
        result['services']['scrapingbee'] = {
            'configured': False
        }
    
    # Check Browserless
    if BROWSERLESS_API_KEY:
        result['services']['browserless'] = {
            'configured': True,
            'key_prefix': BROWSERLESS_API_KEY[:4] + '...'  # Show only prefix for security
        }
        result['cloud_browser_available'] = True
    else:
        result['services']['browserless'] = {
            'configured': False
        }
    
    return result