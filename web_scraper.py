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
    Enhanced function that checks for product tables using HTML parsing.
    Unlike the old version, this actually performs detection instead of returning a fixed message.
    
    Args:
        url: The URL to check
        
    Returns:
        dict: Detection results including found status, class name, and error messages
    """
    logger.info(f"Starting enhanced product detection for: {url}")
    
    # First check URL path patterns (very reliable indicator)
    parsed_url = urlparse(url)
    path_lower = parsed_url.path.lower()
    
    # Check for URL patterns that almost always indicate product pages
    product_url_patterns = [
        # Common product endpoints
        ('/products' in path_lower and (path_lower.endswith('/products') or path_lower.endswith('/products/'))),
        ('/product' in path_lower and not '/product-' in path_lower),  # product directory but not product-info etc.
        ('/catalog' in path_lower and (path_lower.endswith('/catalog') or path_lower.endswith('/catalog/'))),
        ('/shop' in path_lower and (path_lower.endswith('/shop') or path_lower.endswith('/shop/'))),
        ('/items' in path_lower and (path_lower.endswith('/items') or path_lower.endswith('/items/'))),
        
        # Common e-commerce category patterns
        '/collection/' in path_lower,
        '/category/' in path_lower,
        '/department/' in path_lower,
        '/listing/' in path_lower,
        
        # Common e-commerce special product listings
        '/deals/' in path_lower and not '/deals/policy' in path_lower,
        '/sale/' in path_lower and not '/sale/terms' in path_lower,
        '/offer/' in path_lower and not '/offer/terms' in path_lower,
        
        # Additional common patterns
        '/merchandise/' in path_lower,
        '/store/' in path_lower,
    ]
    
    # If any pattern matches, we can confidently say this is a product page
    if any(product_url_patterns):
        logger.info(f"URL pattern indicates product page: {url}")
        return {
            'found': True,
            'class_name': 'product-page-url-pattern',
            'detection_method': 'url_pattern_analysis',
            'message': f'Product page detected from URL pattern: {path_lower}',
            'is_test_domain': False,
            'confidence': 'high'
        }
    
    # Try to get actual HTML content
    try:
        # Set a short timeout to prevent hanging
        timeout = 3  # 3 seconds max
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, timeout=timeout, headers=headers)
        if response.status_code != 200:
            logger.warning(f"Got status code {response.status_code} for {url}")
            return {
                'found': None,
                'class_name': None,
                'detection_method': 'http_status_error',
                'message': f'HTTP request failed with status {response.status_code}',
                'is_test_domain': False
            }
            
        # Check HTML content for product indicators
        is_product_page = detect_product_page_from_html(response.text, url)
        if is_product_page:
            return {
                'found': True,
                'class_name': 'product-page-html-indicators',
                'detection_method': 'html_analysis',
                'message': 'Product page detected from HTML content analysis',
                'is_test_domain': False,
                'confidence': 'medium'
            }
            
        # If we get here, we didn't find any product indicators
        return {
            'found': False,
            'class_name': None,
            'detection_method': 'html_analysis',
            'message': 'No product indicators found in HTML content',
            'is_test_domain': False,
            'confidence': 'medium' 
        }
    except requests.Timeout:
        logger.warning(f"Request timeout when checking {url}")
        return {
            'found': None,
            'class_name': None,
            'detection_method': 'http_timeout',
            'message': 'HTTP request timed out',
            'is_test_domain': False
        }
    except Exception as e:
        logger.error(f"Error checking for product page: {str(e)}")
        return {
            'found': None,
            'class_name': None,
            'detection_method': 'error',
            'message': f'Error analyzing page: {str(e)}',
            'is_test_domain': False
        }