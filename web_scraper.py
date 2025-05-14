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
    DISABLED: This function no longer performs text analysis to prevent false positives.
    Instead, it always returns a "manual check required" response.
    
    Args:
        url: The URL to check
        
    Returns:
        dict: Results indicating manual check is required
    """
    logger.warning(f"Text analysis detection is disabled to prevent false positives - manual check required for {url}")
    
    # Return a clear result indicating manual check is needed
    return {
        'found': False,
        'error': 'Browser automation unavailable',
        'detection_method': 'text_analysis_disabled',
        'manual_check_required': True,
        'manual_check_message': 'Please visit this page in your browser and check for product tables with "Add to Cart" buttons'
    }