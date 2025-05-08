import trafilatura
import logging
import re
from typing import Dict, Any, Optional, List, Tuple

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_website_text_content(url: str) -> str:
    """
    This function takes a URL and returns the main text content of the website.
    The text content is extracted using trafilatura and is easier to understand.
    
    Args:
        url: The URL to extract text content from
        
    Returns:
        str: Plain text content of the website
    """
    try:
        # Send a request to the website
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            logger.warning(f"Failed to download content from {url}")
            return ""
            
        # Extract the text content
        text = trafilatura.extract(downloaded)
        if not text:
            logger.warning(f"Failed to extract text from {url}")
            return ""
            
        return text
    except Exception as e:
        logger.error(f"Error getting website text content for {url}: {str(e)}")
        return ""

def check_for_product_tables_with_text_analysis(url: str) -> Dict[str, Any]:
    """
    This function analyzes the extracted text content to detect product listings
    using semantic analysis and common product listing patterns.
    
    Args:
        url: The URL to check for product tables
        
    Returns:
        dict: Detection results including confidence score
    """
    try:
        # Get the text content
        text_content = get_website_text_content(url)
        if not text_content:
            return {
                'found': False,
                'error': 'Could not extract text content',
                'detection_method': 'text_analysis_failed'
            }
            
        # Product indicators - common text patterns in product listing pages
        product_indicators = [
            r'product(s)?(\s+list(ing)?)?',
            r'item(s)?(\s+list(ing)?)?',
            r'price',
            r'\$\d+(\.\d{2})?',
            r'add to cart',
            r'buy now',
            r'in stock',
            r'out of stock',
            r'quantity',
            r'product description',
            r'specifications',
            r'features',
            r'reviews',
            r'related products',
            r'more details',
            r'shipping',
            r'delivery',
            r'return policy'
        ]
        
        # Count how many product indicators appear in the text
        indicator_count = 0
        matched_indicators = []
        
        for pattern in product_indicators:
            matches = re.findall(pattern, text_content.lower())
            if matches:
                indicator_count += len(matches)
                matched_indicators.append(pattern)
                
        # Calculate confidence score (0-100) based on indicators found
        # More indicators = higher confidence
        max_indicators = len(product_indicators) * 2  # Allow multiple matches
        confidence_score = min(100, int((indicator_count / max_indicators) * 100))
        
        # Product table likely exists if confidence score above threshold
        found = confidence_score >= 40  # 40% threshold
        
        return {
            'found': found,
            'confidence_score': confidence_score,
            'matched_indicators': matched_indicators,
            'detection_method': 'text_analysis'
        }
    except Exception as e:
        logger.error(f"Error in text analysis for {url}: {str(e)}")
        return {
            'found': False,
            'error': f"Text analysis error: {str(e)}",
            'detection_method': 'text_analysis_error'
        }