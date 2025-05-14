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
    Check if a webpage contains product-related content by analyzing its text.
    This is useful for client-side rendered sites where HTML inspection might not work.
    
    Args:
        url: The URL to check
        
    Returns:
        dict: Results including whether products were detected
    """
    logger.info(f"Analyzing text content from {url} for product detection")
    
    try:
        # Get the text content
        text_content = get_website_text_content(url)
        if not text_content:
            return {
                'found': False,
                'detection_method': 'text_analysis',
                'error': 'No text content could be extracted',
                'confidence_score': 0
            }
        
        # Define product-related keywords and patterns
        product_keywords = [
            # Common product-related terms
            r'product(?:s|)',
            r'item(?:s|)',
            r'catalog',
            r'inventory',
            r'price',
            r'quantity',
            r'manufacturer',
            
            # Specific product types (based on screenshot)
            r'sensor',
            r'valve',
            r'switch',
            r'bearing',
            r'actuator',
            r'digital pressure sensor',
            r'high-pressure hydraulic valve',
            r'industrial ethernet switch',
            r'industrial grade bearing',
            r'linear actuator',
            
            # E-commerce related terms
            r'add to cart',
            r'buy now',
            r'(?:in|out of) stock',
            r'(?:available|unavailable)',
            r'shipping',
            r'delivery',
            
            # Technical product attributes
            r'specifications',
            r'technical details',
            r'dimensions',
            r'weight',
            r'power',
            r'voltage',
            r'frequency',
            r'capacity',
            r'material',
            
            # Product categories
            r'industrial',
            r'electronic',
            r'mechanical',
            r'hydraulic',
            r'components?',
            r'supplies',
            r'equipment',
            r'parts?',
            r'accessories'
        ]
        
        # Check for product-related terms in the content
        found_product_terms = []
        confidence_score = 0
        
        for keyword in product_keywords:
            pattern = re.compile(keyword, re.IGNORECASE)
            matches = pattern.findall(text_content)
            if matches:
                found_product_terms.extend(matches)
                # Increase confidence score with each match
                match_score = len(matches) * 0.05
                confidence_score += match_score
                if len(matches) > 1:
                    logger.info(f"Found {len(matches)} instances of '{keyword}' pattern, adding {match_score:.2f} to score")
                
        # Limit the confidence score to 1.0
        confidence_score = min(confidence_score, 1.0)
        
        # Check for table-like structures in the text
        table_indicators = [
            # Column headers
            r'product\s+name',
            r'product\s+id',
            r'product\s+number',
            r'part\s+number',
            r'quantity\s+available',
            r'price\s+\(usd\)',
            r'manufacturer',
            r'description',
            r'specifications',
            r'stock\s+status',
            r'category',
            r'model',
            r'sku',
            
            # Product list headers
            r'products\s+list',
            r'catalog\s+items',
            r'available\s+products',
            r'search\s+results',
            r'browse\s+catalog',
            
            # Grid structure terms
            r'product\s+grid',
            r'items\s+grid',
            r'products\s+view',
            
            # Patterns that indicate multiple products
            r'showing\s+\d+\s+(?:of|out of|from)\s+\d+\s+products',
            r'\d+\s+products\s+found',
            r'results\s+\d+-\d+\s+of\s+\d+',
            
            # Common filter terms for product tables
            r'filter\s+by',
            r'sort\s+by',
            r'price\s+range',
            r'filter\s+results'
        ]
        
        has_table_structure = False
        table_structure_matches = []
        
        for indicator in table_indicators:
            if re.search(indicator, text_content, re.IGNORECASE):
                match = re.search(indicator, text_content, re.IGNORECASE)
                if match:
                    has_table_structure = True
                    table_structure_matches.append(match.group(0))
                    confidence_score += 0.1  # Bonus for table structure
                    
                    # If we find multiple table structure indicators, increase confidence
                    if len(table_structure_matches) >= 3:
                        confidence_score += 0.2  # Extra bonus for multiple indicators
                        logger.info(f"Multiple table structure indicators found: {table_structure_matches[:3]}")
                        break
                
        # Determine if this is likely a product page
        is_product_page = confidence_score >= 0.3 or (has_table_structure and confidence_score >= 0.2)
        
        # Check the URL structure for additional confidence
        parsed_url = urlparse(url)
        path = parsed_url.path.lower()
        
        # Strong URL indicators of product pages
        primary_url_indicators = ['/products', '/catalog', '/shop', '/inventory']
        # Secondary URL indicators that contribute but aren't definitive
        secondary_url_indicators = ['/item', '/part', '/component', '/accessory', '/detail']
        
        # Check primary indicators (these are very strong signals)
        for indicator in primary_url_indicators:
            if indicator in path:
                confidence_score += 0.3  # Significant boost
                is_product_page = True   # URL strongly indicates a product page
                logger.info(f"URL path contains strong product indicator: {indicator}")
                break
        
        # Check secondary indicators
        for indicator in secondary_url_indicators:
            if indicator in path:
                confidence_score += 0.1  # Smaller boost
                # Don't auto-set is_product_page to True for secondary indicators
                logger.info(f"URL path contains secondary product indicator: {indicator}")
                break
        
        # Check for product IDs or SKUs in the URL (common for product pages)
        if re.search(r'/p/\d+', path) or re.search(r'/product[/_-]id/\d+', path) or re.search(r'/sku/[\w\d]+', path):
            confidence_score += 0.2
            is_product_page = True
            logger.info(f"URL likely contains product ID or SKU")
        
        # Format and return the result
        return {
            'found': is_product_page,
            'detection_method': 'text_analysis',
            'confidence_score': round(confidence_score, 2),
            'found_terms': found_product_terms[:10],  # Limit to first 10 matches
            'has_table_structure': has_table_structure,
            'table_structure_indicators': table_structure_matches[:5] if table_structure_matches else [],
            'url_indicators': [i for i in primary_url_indicators if i in path]
        }
        
    except Exception as e:
        logger.error(f"Error during text analysis for {url}: {str(e)}")
        return {
            'found': False,
            'detection_method': 'text_analysis',
            'error': str(e),
            'confidence_score': 0
        }