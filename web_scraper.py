import trafilatura
import logging
import re
import requests
from bs4 import BeautifulSoup
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

def get_html_content(url: str, timeout: Optional[int] = 10) -> Optional[str]:
    """
    Get raw HTML content from a URL with proper error handling.
    
    Args:
        url: The URL to fetch
        timeout: Request timeout in seconds
        
    Returns:
        str or None: HTML content or None if failed
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }
        
        response = requests.get(url, headers=headers, timeout=timeout)
        if response.status_code == 200:
            return response.text
        else:
            logger.warning(f"Failed to get HTML content from {url}. Status code: {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"Error fetching HTML content from {url}: {str(e)}")
        return None

def analyze_html_structure(url: str) -> Dict[str, Any]:
    """
    Analyze HTML structure for product table indicators using BeautifulSoup.
    Looks for common HTML structures found in product tables.
    
    Args:
        url: The URL to analyze
        
    Returns:
        dict: Analysis results
    """
    try:
        html_content = get_html_content(url)
        if not html_content:
            return {
                'found': False,
                'error': 'Could not fetch HTML content',
                'detection_method': 'html_structure_analysis_failed'
            }
            
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Product table structure indicators
        structure_indicators = {
            'product_grid': ['product-grid', 'products-grid', 'grid-view', 'grid-container'],
            'product_list': ['product-list', 'products-list', 'list-view', 'listing'],
            'product_table': ['product-table', 'products-table', 'table-view'],
            'product_container': ['product-container', 'products-container', 'item-container'],
            'product_card': ['product-card', 'product-item', 'product-box', 'item-card'],
            'product_row': ['product-row', 'row-item', 'item-row'],
            'product_pricing': ['price-container', 'product-price', 'price-box', 'price-wrapper']
        }
        
        # Results tracking
        found_indicators = {}
        total_structures = 0
        
        # Check class names in various elements for product table indicators
        for element_type in ['div', 'ul', 'table', 'section', 'article']:
            elements = soup.find_all(element_type, class_=True)
            
            for element in elements:
                # Handle element class attribute safely
                try:
                    class_attr = element.get('class', [])
                    if class_attr is None:
                        class_attr = []
                    elif isinstance(class_attr, str):
                        class_attr = [class_attr]
                    
                    # Convert list to string
                    element_classes = ' '.join([str(c) for c in class_attr if c]).lower()
                except Exception as e:
                    logger.warning(f"Error processing class attribute: {e}")
                    element_classes = ""
                
                # Check against structure indicators
                for indicator_type, indicator_patterns in structure_indicators.items():
                    for pattern in indicator_patterns:
                        if pattern.lower() in element_classes:
                            if indicator_type not in found_indicators:
                                found_indicators[indicator_type] = []
                            
                            # Record details about the found structure safely
                            element_details = {
                                'class': element_classes,
                                'pattern': pattern
                            }
                            
                            # Add element name if available
                            try:
                                if hasattr(element, 'name'):
                                    element_details['element'] = element.name
                            except Exception:
                                element_details['element'] = 'unknown'
                                
                            # Get child count safely
                            try:
                                if hasattr(element, 'find_all'):
                                    element_details['child_count'] = len(element.find_all())
                                else:
                                    element_details['child_count'] = 0
                            except Exception:
                                element_details['child_count'] = 0
                                
                            found_indicators[indicator_type].append(element_details)
                            
                            total_structures += 1
        
        # Calculate confidence based on the number and types of structures found
        confidence_score = min(100, total_structures * 10)  # 10 points per structure found
        
        # Check for specific product indicators in the content
        price_regex = r'[\$€£]\s*\d+(\.\d{2})?'
        price_elements = soup.find_all(text=re.compile(price_regex))
        
        # Add pricing to the confidence score
        if price_elements:
            confidence_score = min(100, confidence_score + 20)
            found_indicators['price_elements'] = len(price_elements)
        
        # Look for product images
        product_images = 0
        for img in soup.find_all('img'):
            # Get attributes safely
            try:
                img_src = ""
                if hasattr(img, 'get'):
                    src_attr = img.get('src')
                    if src_attr is not None:
                        img_src = str(src_attr)
                    
                img_alt = ""
                if hasattr(img, 'get'):
                    alt_attr = img.get('alt')
                    if alt_attr is not None:
                        img_alt = str(alt_attr)
                
                # Safely check for product-related terms in attributes
                if ('product' in img_src.lower() if img_src else False) or \
                   ('product' in img_alt.lower() if img_alt else False):
                    product_images += 1
            except Exception as e:
                logger.warning(f"Error processing image element: {e}")
        
        if product_images > 0:
            found_indicators['product_images'] = product_images
            confidence_score = min(100, confidence_score + (10 if product_images > 5 else 5))
        
        # Product table likely exists if confidence score above threshold
        found = confidence_score >= 30  # 30% threshold
        
        return {
            'found': found,
            'confidence_score': confidence_score,
            'found_indicators': found_indicators,
            'detection_method': 'html_structure_analysis'
        }
    except Exception as e:
        logger.error(f"Error in HTML structure analysis for {url}: {str(e)}")
        return {
            'found': False,
            'error': f"HTML structure analysis error: {str(e)}",
            'detection_method': 'html_structure_analysis_error'
        }

def check_for_product_tables_with_text_analysis(url: str) -> Dict[str, Any]:
    """
    This function analyzes the extracted text content and HTML structure to detect product listings
    using semantic analysis and common product listing patterns.
    Uses a dual-approach strategy combining text analysis and HTML structure.
    
    Args:
        url: The URL to check for product tables
        
    Returns:
        dict: Detection results including confidence score
    """
    try:
        # Strategy 1: Text-based analysis
        text_content = get_website_text_content(url)
        if not text_content:
            logger.warning(f"Text-based analysis failed for {url}, falling back to HTML structure analysis only")
            return analyze_html_structure(url)
            
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
        text_confidence = min(100, int((indicator_count / max_indicators) * 100))
        
        # Strategy 2: HTML structure analysis
        html_result = analyze_html_structure(url)
        html_confidence = html_result.get('confidence_score', 0)
        
        # Combined analysis with weighted approach
        # Text analysis is 40%, structure analysis is 60% of final score
        combined_confidence = (text_confidence * 0.4) + (html_confidence * 0.6)
        
        # Product table likely exists if combined confidence score above threshold
        found = combined_confidence >= 35  # 35% threshold
        
        return {
            'found': found,
            'confidence_score': int(combined_confidence),
            'text_confidence': text_confidence,
            'html_confidence': html_confidence,
            'text_indicators': matched_indicators,
            'html_indicators': html_result.get('found_indicators', {}),
            'detection_method': 'combined_text_html_analysis'
        }
    except Exception as e:
        logger.error(f"Error in combined text/HTML analysis for {url}: {str(e)}")
        return {
            'found': False,
            'error': f"Combined analysis error: {str(e)}",
            'detection_method': 'combined_analysis_error'
        }