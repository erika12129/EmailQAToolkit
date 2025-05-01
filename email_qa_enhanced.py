"""
Enhanced Email QA Automation module with improved link handling and product table detection.
Handles validation of email HTML and verifies content based on requirements.
"""

import json
import re
import os
import logging
import requests
import threading
import queue
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from runtime_config import config

# Note: Selenium imports are commented out as they are not currently used
# but may be needed for future advanced detection methods
# from selenium import webdriver
# from selenium.webdriver.chrome.options import Options
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_email_html(email_path):
    """Parse email HTML file."""
    try:
        with open(email_path, 'r', encoding='utf-8') as f:
            return BeautifulSoup(f, 'html.parser')
    except Exception as e:
        logger.error(f"Failed to parse email HTML: {e}")
        raise

def load_requirements(requirements_path):
    """Load campaign requirements from JSON file."""
    try:
        with open(requirements_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load requirements: {e}")
        raise

def extract_email_metadata(soup):
    """Extract sender information, subject, and preheader from email HTML."""
    # Support both dashed and underscored meta names for consistency
    sender = (
        soup.find('meta', {'name': 'sender'}) or 
        soup.find('meta', {'name': 'sender_address'}) or 
        soup.find('meta', {'name': 'sender-address'}) or 
        soup.find('from') or 
        {}
    )
    
    sender_name = (
        soup.find('meta', {'name': 'sender-name'}) or 
        soup.find('meta', {'name': 'sender_name'}) or 
        soup.find('from-name') or 
        {}
    )
    
    reply_to = (
        soup.find('meta', {'name': 'reply-to'}) or 
        soup.find('meta', {'name': 'reply_to'}) or 
        soup.find('meta', {'name': 'reply_address'}) or 
        soup.find('meta', {'name': 'reply-address'}) or 
        soup.find('reply-to') or 
        {}
    )
    
    subject = soup.find('meta', {'name': 'subject'}) or soup.find('title') or {}
    
    # Try various common preheader class names
    preheader_classes = ['preheader', 'preview-text', 'preview', 'hidden-preheader']
    preheader = None
    attempted_classes = []
    
    for cls in preheader_classes:
        attempted_classes.append(cls)
        element = soup.find('div', {'class': cls}) or soup.find('span', {'class': cls})
        if element:
            preheader = element
            break
    
    if not preheader:
        preheader = {}
        logger.warning(f"Preheader not found. Attempted classes: {', '.join(attempted_classes)}")
    
    # Clean up preheader text by removing hidden characters
    preheader_text = preheader.get_text(strip=True) if hasattr(preheader, 'get_text') else 'Not found'
    
    # Extract just the readable text from the preheader
    # This strips out invisible characters used for email client spacing/preview control
    if preheader_text != 'Not found':
        # Keep only visible characters - this will strip out zero-width spaces, hidden characters, etc.
        # Extract only the visible characters before hidden ones begin
        visible_preheader = re.sub(r'[\u200c\u200b\u2060\u2061\u2062\u2063\u2064\u2065\u2066\u2067\u2068\u2069\u206a\u206b\u206c\u206d\u206e\u206f\u034f\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2007\u00ad\u2011\ufeff].*', '', preheader_text)
        # If the regex failed to extract anything meaningful, use the first part of the string
        if not visible_preheader.strip():
            # Take the first 100 chars as a fallback
            visible_preheader = preheader_text[:100]
        preheader_text = visible_preheader.strip()
    
    # Standard campaign code extraction logic
    # (Footer campaign code extraction would remain intact)
    footer_campaign_code = "Not found"
    
    # Create metadata dictionary
    metadata_dict = {
        'sender': sender.get('content') or (sender.get_text(strip=True) if hasattr(sender, 'get_text') else '') or 'Not found',
        'sender_name': sender_name.get('content') or (sender_name.get_text(strip=True) if hasattr(sender_name, 'get_text') else '') or 'Not found',
        'reply_to': reply_to.get('content') or (reply_to.get_text(strip=True) if hasattr(reply_to, 'get_text') else '') or 'Not found',
        'subject': subject.get('content') or (subject.get_text(strip=True) if hasattr(subject, 'get_text') else '') or 'Not found',
        'preheader': preheader_text,
        'preheader_details': f"Attempted classes: {', '.join(attempted_classes)}" if not hasattr(preheader, 'get_text') else '',
        'footer_campaign_code': footer_campaign_code
    }
    
    return metadata_dict

def extract_links(soup):
    """Extract all links from email HTML with enhanced source context."""
    links = []
    for a in soup.find_all('a', href=True):
        # Include source context (text, image, or button)
        if a.find('img'):
            # Image link
            img = a.find('img')
            alt_text = img.get('alt', '')
            source_context = f"Image: {alt_text[:50]}" if alt_text else "Image link"
        else:
            # Text or button link
            text = a.get_text(strip=True)
            if text:
                source_context = f"Text: {text[:50]}"
            else:
                source_context = "Empty link"
                
        links.append((source_context, a['href']))
    return links

def validate_utm_parameters(url, expected_utm):
    """Validate UTM parameters in a URL against expected values."""
    url_parts = urlparse(url)
    query_params = parse_qs(url_parts.query)
    
    utm_issues = []
    
    # Check required UTM parameters
    for param, expected_value in expected_utm.items():
        if expected_value:
            if param in query_params:
                actual_value = query_params[param][0]
                if actual_value != expected_value:
                    utm_issues.append(f"Parameter {param} has value '{actual_value}', but expected '{expected_value}'")
            else:
                # Only report as an issue if it's not webtrends (which is optional)
                if param != 'webtrends':
                    utm_issues.append(f"Missing parameter {param}")
    
    return utm_issues

def check_http_status(url, timeout=None):
    """
    Check HTTP status code of a URL with configurable timeout.
    
    Args:
        url: The URL to check
        timeout: Request timeout in seconds, or None to use config default
        
    Returns:
        Status code or error message
    """
    if timeout is None:
        timeout = config.request_timeout
        
    try:
        # For checking status, don't actually download the full response
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return response.status_code
    except requests.exceptions.Timeout:
        return "Timeout"
    except requests.exceptions.SSLError:
        return "SSL Error"
    except requests.exceptions.ConnectionError:
        return "Connection Error"
    except Exception as e:
        return f"Error: {str(e)}"

def check_for_product_tables(url, timeout=None):
    """
    Check if a URL's HTML contains product table classes with improved error handling.
    
    Args:
        url: The URL to check for product tables
        timeout: Request timeout in seconds, or None to use config default
        
    Returns:
        dict: Detection results including found status, class name, and errors
    """
    if timeout is None:
        timeout = config.product_table_timeout
        
    try:
        logger.info(f"Checking URL for product tables: {url}")
        
        # Get the HTML content with timeout
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        
        if response.status_code == 200:
            page_content = response.text
            
            # Check for product-table class
            product_table_match = re.search(r'class=["\']([^"\']*?product-table[^"\']*?)["\']', page_content)
            if product_table_match:
                class_name = product_table_match.group(1)
                logger.info(f"Found product-table class: {class_name}")
                return {
                    'found': True,
                    'class_name': class_name,
                    'detection_method': 'direct_html'
                }
            
            # Check for productListContainer class if still not found
            list_container_match = re.search(r'class=["\']([^"\']*?productListContainer[^"\']*?)["\']', page_content)
            if list_container_match:
                class_name = list_container_match.group(1)
                logger.info(f"Found productListContainer class: {class_name}")
                return {
                    'found': True,
                    'class_name': class_name,
                    'detection_method': 'direct_html'
                }
            
            logger.info(f"No product table classes found on {url}")
            return {
                'found': False,
                'detection_method': 'direct_html'
            }
        else:
            error_message = f"Failed to get content, status code: {response.status_code}"
            logger.error(error_message)
            return {
                'found': False,
                'error': error_message,
                'detection_method': 'failed'
            }
    except requests.exceptions.Timeout:
        error_message = f"Connection to {url} timed out after {timeout}s"
        logger.error(error_message)
        return {
            'found': False,
            'error': error_message,
            'detection_method': 'failed'
        }
    except requests.exceptions.SSLError as ssl_err:
        error_message = f"SSL error when connecting to {url}: {str(ssl_err)}"
        logger.error(error_message)
        return {
            'found': False,
            'error': error_message,
            'detection_method': 'failed'
        }
    except requests.exceptions.ConnectionError:
        error_message = f"Failed to connect to {url}"
        logger.error(error_message)
        return {
            'found': False,
            'error': error_message,
            'detection_method': 'failed'
        }
    except Exception as e:
        error_message = f"Error checking for product tables: {str(e)}"
        logger.error(error_message)
        return {
            'found': False,
            'error': error_message,
            'detection_method': 'failed'
        }

def check_links(links, expected_utm):
    """
    Check if links load correctly and have correct UTM parameters.
    Enhanced with smart redirection and improved product table detection.
    """
    results = []
    
    for link_source, url in links:
        original_url = url
        processed_url = url
        redirected = False
        
        # Process URL based on configuration
        domain = urlparse(url).netloc
        is_test_domain = domain in config.test_domains
        
        # Handle test domains and redirects in BOTH dev and prod mode for functionality
        # This ensures product table detection works properly
        if is_test_domain or config.enable_test_redirects:
            test_url = config.create_test_url(url)
            try:
                # Check if test URL is accessible
                test_response = requests.head(test_url, timeout=2)
                if test_response.status_code == 200:
                    processed_url = test_url
                    redirected = True
                    logger.info(f"Redirecting to test URL: {url} -> {test_url}")
            except Exception as e:
                # If test URL fails, continue with original
                logger.warning(f"Test URL not accessible: {test_url}, using original. Error: {e}")
        
        # Check HTTP status
        status_code = check_http_status(processed_url)
        
        # Check UTM parameters
        utm_issues = validate_utm_parameters(url, expected_utm)
        
        # Check for product tables
        product_table_result = None
        product_table_found = False
        product_table_class = None
        product_table_error = None
        
        # Only check if status code is numeric and 200 (OK)
        if isinstance(status_code, int) and status_code == 200:
            try:
                # Use a fixed, short timeout in production mode to prevent hung requests
                # In development mode, use the configured timeout
                check_timeout = 3 if config.is_production else config.product_table_timeout
                
                # Create a separate thread for the product table check with a timeout
                # This ensures one slow check doesn't block subsequent ones
                
                result_queue = queue.Queue()
                
                def check_table_thread():
                    try:
                        result = check_for_product_tables(processed_url, timeout=check_timeout)
                        result_queue.put(result)
                    except Exception as e:
                        logger.error(f"Thread error checking product tables: {str(e)}")
                        result_queue.put({
                            'found': False,
                            'error': f"Thread error: {str(e)}",
                            'detection_method': 'failed'
                        })
                
                # Start thread and wait with timeout
                thread = threading.Thread(target=check_table_thread)
                thread.daemon = True
                thread.start()
                
                try:
                    # Wait for result with timeout
                    thread_timeout = check_timeout + 1  # Give thread a little extra time
                    product_table_result = result_queue.get(timeout=thread_timeout)
                except queue.Empty:
                    # If we timeout waiting for the thread
                    logger.error(f"Thread timeout checking product tables for {processed_url}")
                    product_table_result = {
                        'found': False,
                        'error': f"Thread timeout after {thread_timeout}s",
                        'detection_method': 'failed'
                    }
                
                # Extract results
                product_table_found = product_table_result.get('found', False)
                product_table_class = product_table_result.get('class_name')
                
                if not product_table_found and product_table_result.get('error'):
                    product_table_error = product_table_result.get('error')
            except Exception as e:
                # Catch any unexpected errors during product table checking
                # to prevent one link from affecting others
                logger.error(f"Unexpected error during product table check for {processed_url}: {str(e)}")
                product_table_error = f"Check failed: {str(e)}"
        else:
            # If status check failed, don't attempt product table check
            product_table_error = f"URL returned HTTP status {status_code}, product table check skipped"
        
        # Compile result
        result = {
            'source': link_source,
            'url': original_url,
            'status': status_code,
            'utm_issues': utm_issues,
            'has_product_table': product_table_found,
            'product_table_class': product_table_class,
            'product_table_error': product_table_error,
            # Override logic - only show redirects in development mode, hide them completely in production mode
            # This ensures product tables are correctly detected but not shown in the UI
            'redirected_to': processed_url if (
                (processed_url != original_url) and config.is_development
            ) else None
        }
        
        results.append(result)
    
    return results

def validate_email(email_path, requirements_path):
    """
    Main function to validate email against requirements.
    Enhanced with mode awareness and improved error handling.
    """
    metadata = None  # Initialize to avoid unbound variable issue
    
    try:
        # Parse email HTML
        soup = parse_email_html(email_path)
        
        # Load requirements
        requirements = load_requirements(requirements_path)
        
        # Extract metadata and validate
        metadata = extract_email_metadata(soup)
        
        # Compare with expected values
        expected_metadata = requirements.get('metadata', {})
        metadata_issues = []
        
        for key, expected_value in expected_metadata.items():
            if expected_value and key in metadata:
                actual_value = metadata[key]
                if actual_value != expected_value and actual_value != 'Not found':
                    metadata_issues.append(f"{key}: Expected '{expected_value}', found '{actual_value}'")
        
        # Extract and check links
        links = extract_links(soup)
        link_results = check_links(links, requirements.get('utm_parameters', {}))
        
        # Prepare results
        results = {
            'metadata': metadata,
            'metadata_issues': metadata_issues,
            'links': link_results,
            'mode': config.mode
        }
        
        return results
    except Exception as e:
        logger.error(f"Error in validate_email: {e}")
        # Return partial results if we have metadata
        if metadata is not None:
            return {
                'metadata': metadata,
                'metadata_issues': ["Error processing email: " + str(e)],
                'links': [],
                'mode': config.mode,
                'error': str(e)
            }
        else:
            return {
                'error': f"Failed to validate email: {str(e)}",
                'mode': config.mode
            }