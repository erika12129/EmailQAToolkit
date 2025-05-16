"""
Web scraper module for Email QA System.
Uses Trafilatura for extracting text content from websites for analysis.
Enhanced with product detection capabilities.
"""

import re
import logging
import trafilatura
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
import time

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

def detect_product_page_from_html(html_content, url):
    """
    Analyze HTML content to detect if this is a product page.
    
    Args:
        html_content: The HTML content to analyze
        url: The URL being checked (for logging)
        
    Returns:
        bool: True if it looks like a product page, False otherwise
    """
    if not html_content:
        return False
        
    try:
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Common product-related classes and patterns
        product_class_patterns = [
            'product-', 'productTable', 'productList', 'productCard', 'productGrid',
            'product-table', 'product-list', 'product-card', 'product-grid',
            'product-container', 'productContainer',
            'products-wrapper', 'productsWrapper',
            'products-section', 'productsSection',
            'item-container', 'item-list', 'item-grid',
            'catalog', 'shop-container'
        ]
        
        # Check for elements with product-related classes
        for pattern in product_class_patterns:
            elements = soup.select(f'[class*="{pattern}"]')
            if elements:
                logger.info(f"Found product class pattern '{pattern}' in {url}")
                return True
                
        # Look for product-related text in the page
        product_indicators = [
            'Add to Cart', 'Add to Bag', 'Buy Now', 'Add to Basket',
            'Price:', 'Regular price:', 'Sale price:', 'Original price:',
            'In Stock', 'Out of Stock', 'Usually ships in', 
            'Product Details', 'Product Description', 'Specifications',
            'SKU:', 'Item #:', 'Model #:', 'Product #:',
            'Availability:', 'Quantity:', 'Shipping:',
            'Related Products', 'Similar Items', 'You May Also Like'
        ]
        
        # Case-insensitive search for product indicators in the text
        page_text = soup.get_text().lower()
        for indicator in product_indicators:
            if indicator.lower() in page_text:
                # We want at least two different indicators to reduce false positives
                count = sum(1 for ind in product_indicators if ind.lower() in page_text)
                if count >= 2:  # At least two different indicators
                    logger.info(f"Found multiple product text indicators in {url}")
                    return True
                    
        # Check for structured data that indicates products (JSON-LD)
        script_tags = soup.find_all('script', {'type': 'application/ld+json'})
        for script in script_tags:
            if script.string and ('Product' in script.string or 'product' in script.string.lower()):
                logger.info(f"Found product structured data in {url}")
                return True
                
        # Check HTML meta tags for product indicators
        meta_tags = soup.find_all('meta')
        for tag in meta_tags:
            content = tag.get('content', '').lower()
            if content and ('product' in content or 'shop' in content or 'store' in content):
                logger.info(f"Found product meta tag in {url}")
                return True
                
        return False
    except Exception as e:
        logger.error(f"Error checking product page from HTML: {str(e)}")
        return False

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