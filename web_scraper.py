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
    Analyze HTML structure for product table classes using BeautifulSoup.
    Specifically looks for "product-table*" or "*productListContainer" in div classes.
    
    Args:
        url: The URL to analyze
        
    Returns:
        dict: Analysis results with found class name
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
        
        # Target specific class patterns
        product_table_pattern = re.compile(r'product-table.*', re.IGNORECASE)
        product_list_container_pattern = re.compile(r'.*productListContainer.*', re.IGNORECASE)
        
        # Look for divs with the specific class patterns we need
        for div in soup.find_all('div', class_=True):
            try:
                # Safely extract class attributes
                try:
                    # Try to get the class attribute
                    if hasattr(div, 'attrs') and isinstance(div.attrs, dict) and 'class' in div.attrs:
                        classes = div.attrs['class']
                    elif hasattr(div, 'get'):
                        # Try to use the get method if it exists
                        classes = div.get('class')
                    else:
                        # Skip if we can't get the classes
                        continue
                        
                    # Skip if no classes found
                    if not classes:
                        continue
                        
                    # Handle if class is already a string
                    if isinstance(classes, str):
                        class_str = classes
                    elif isinstance(classes, list):
                        # Join classes into a string
                        class_str = ' '.join([str(c) for c in classes if c])
                    else:
                        # Convert unknown type to string
                        class_str = str(classes)
                except Exception as e:
                    logger.warning(f"Error getting class attribute: {e}")
                    continue
                
                # Check for product-table pattern first
                match_product_table = product_table_pattern.search(class_str)
                if match_product_table:
                    try:
                        found_class = match_product_table.group(0)
                        logger.info(f"Found product-table class: {found_class}")
                        
                        return {
                            'found': True,
                            'class_name': found_class,
                            'element_type': 'div',
                            'detection_method': 'html_structure_analysis'
                        }
                    except Exception as e:
                        logger.warning(f"Error extracting product-table match: {e}")
                
                # Check for productListContainer pattern
                match_product_list = product_list_container_pattern.search(class_str)
                if match_product_list:
                    try:
                        found_class = match_product_list.group(0)
                        logger.info(f"Found productListContainer class: {found_class}")
                        
                        return {
                            'found': True,
                            'class_name': found_class,
                            'element_type': 'div',
                            'detection_method': 'html_structure_analysis'
                        }
                    except Exception as e:
                        logger.warning(f"Error extracting productListContainer match: {e}")
            except Exception as e:
                logger.warning(f"Error processing div classes: {e}")
                continue
        
        # If we got here, no matching classes were found
        logger.info("No product table classes found in HTML")
        return {
            'found': False,
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
    This function primarily uses HTML structure analysis to find product table classes.
    Falls back to text analysis only if HTML structure analysis fails.
    
    Args:
        url: The URL to check for product tables
        
    Returns:
        dict: Detection results
    """
    try:
        # Primary method: HTML structure analysis to find specific class names
        html_result = analyze_html_structure(url)
        
        # If we found a matching class, return the result directly
        if html_result.get('found', False):
            logger.info(f"Found product table class via HTML analysis: {html_result.get('class_name')}")
            return html_result
        
        # Fallback method: Check the text content for product indicators
        text_content = get_website_text_content(url)
        if not text_content:
            logger.warning(f"Text analysis fallback failed for {url} - no content extracted")
            return {
                'found': False,
                'detection_method': 'text_analysis_failed'
            }
        
        # Look for product table related keywords in the text
        product_keywords = [
            'product table', 
            'product list', 
            'product grid', 
            'productListContainer',
            'product-table'
        ]
        
        for keyword in product_keywords:
            if keyword.lower() in text_content.lower():
                logger.info(f"Found product table keyword in text: {keyword}")
                return {
                    'found': True,
                    'keyword': keyword,
                    'detection_method': 'text_analysis'
                }
        
        # If we got here, no product tables were detected by any method
        return {
            'found': False,
            'detection_method': 'combined_analysis'
        }
    except Exception as e:
        logger.error(f"Error in product table detection for {url}: {str(e)}")
        return {
            'found': False,
            'error': f"Detection error: {str(e)}",
            'detection_method': 'error'
        }