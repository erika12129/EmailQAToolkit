"""
Web scraper module for Email QA System.
Uses Trafilatura for extracting text content from websites for analysis.
"""

import re
import logging
import trafilatura
from urllib.parse import urlparse

# Setup logging
logger = logging.getLogger(__name__)

def get_website_text_content(url: str) -> str:
    """
    Extract the main text content of a website using Trafilatura.
    
    Args:
        url: The URL to extract content from
        
    Returns:
        str: The extracted text content
    """
    try:
        # Send a request to the website
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            logger.warning(f"Failed to download content from {url}")
            return ""
            
        # Extract the main text content
        text = trafilatura.extract(downloaded)
        if not text:
            logger.warning(f"No text content could be extracted from {url}")
            return ""
            
        return text
    except Exception as e:
        logger.error(f"Error extracting content from {url}: {str(e)}")
        return ""

def check_for_product_tables_with_text_analysis(url: str) -> dict:
    """
    Function that ALWAYS returns a standardized message about browser automation
    being unavailable, and NEVER relies on text analysis fallbacks.
    
    Args:
        url: The URL to check
        
    Returns:
        dict: Standard response indicating browser automation is unavailable
    """
    logger.info(f"Browser automation unavailable message for {url} - no text analysis performed")
    
    # IMPORTANT: Always return the standard message that browser automation is unavailable
    # This ensures we NEVER perform any text-based analysis or URL pattern matching
    return {
        'found': None,
        'class_name': None, 
        'detection_method': 'browser_unavailable',
        'message': 'Unknown - Browser automation unavailable - manual verification required',
        'is_test_domain': False
    }