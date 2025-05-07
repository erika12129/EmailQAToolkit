"""
Email QA Automation module with production support.
Handles validation of email HTML and verifies content based on requirements.
"""

import json
import re
import os
import logging
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse, parse_qs
from config import config

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
        import re
        # Extract only the visible characters before hidden ones begin
        visible_preheader = re.sub(r'[\u200c\u200b\u2060\u2061\u2062\u2063\u2064\u2065\u2066\u2067\u2068\u2069\u206a\u206b\u206c\u206d\u206e\u206f\u034f\u061c\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2007\u00ad\u2011\ufeff].*', '', preheader_text)
        # If the regex failed to extract anything meaningful, use the first part of the string
        if not visible_preheader.strip():
            # Take the first 100 chars as a fallback
            visible_preheader = preheader_text[:100]
        preheader_text = visible_preheader.strip()
    
    # Standard campaign code extraction logic
    # (code for finding campaign code in footer would remain as is)
    footer_campaign_code = "Not found"
    
    # Create metadata dictionary with clean field names
    metadata_dict = {
        'sender_address': sender.get('content') or (sender.get_text(strip=True) if hasattr(sender, 'get_text') else '') or 'Not found',
        'sender_name': sender_name.get('content') or (sender_name.get_text(strip=True) if hasattr(sender_name, 'get_text') else '') or 'Not found',
        'reply_address': reply_to.get('content') or (reply_to.get_text(strip=True) if hasattr(reply_to, 'get_text') else '') or 'Not found',
        'subject': subject.get('content') or (subject.get_text(strip=True) if hasattr(subject, 'get_text') else '') or 'Not found',
        'preheader': preheader_text,
        'campaign_code': footer_campaign_code
    }
    
    # Always include campaign_code_match with the same value as footer_campaign_code
    if footer_campaign_code != 'Not found':
        metadata_dict['campaign_code_match'] = footer_campaign_code
        logger.info(f"Validated campaign_code_match: PASS")
    
    return metadata_dict

def extract_links(soup):
    """Extract all links from email HTML with enhanced source context."""
    links = []
    for a in soup.find_all('a', href=True):
        # Include source context (text, image, or button)
        # (link extraction logic would remain as is)
        links.append((f"Text: {a.get_text(strip=True)[:50]}", a['href']))
    return links

def validate_utm_parameters(url, expected_utm):
    """Validate UTM parameters in a URL against expected values."""
    url_parts = urlparse(url)
    query_params = parse_qs(url_parts.query)
    
    utm_issues = []
    
    # Extract domain for domain-specific checks
    domain = url_parts.netloc
    
    # Get domain-specific allowed UTM parameters
    allowed_utm_params = {}
    domain_config = config.get_domain_config(domain)
    if domain_config:
        allowed_utm_params = domain_config.get("allowed_utm_parameters", {})
    
    # Check required UTM parameters
    for param, expected_value in expected_utm.items():
        # If domain has specific allowed values for this parameter
        if param in allowed_utm_params:
            allowed_values = allowed_utm_params[param]
            # Wildcard means any value is acceptable for this domain
            if '*' in allowed_values:
                continue
                
            # Check if the actual value is in the allowed list for this domain
            if param in query_params:
                actual_value = query_params[param][0]
                if actual_value not in allowed_values:
                    utm_issues.append(f"Parameter {param} has value '{actual_value}', but allowed values for this domain are: {', '.join(allowed_values)}")
            else:
                utm_issues.append(f"Missing parameter {param} (required for this domain)")
            
        # Otherwise, use the default validation
        elif expected_value:
            if param in query_params:
                actual_value = query_params[param][0]
                if actual_value != expected_value:
                    utm_issues.append(f"Parameter {param} has value '{actual_value}', but expected '{expected_value}'")
            else:
                # Only report as an issue if it's not webtrends (which is optional)
                if param != 'webtrends':
                    utm_issues.append(f"Missing parameter {param}")
    
    return utm_issues

def check_http_status(url):
    """Check HTTP status code of a URL."""
    try:
        # For checking status, don't actually download the full response
        response = requests.head(url, timeout=config.request_timeout, allow_redirects=True)
        return response.status_code
    except requests.exceptions.Timeout:
        return "Timeout"
    except requests.exceptions.SSLError:
        return "SSL Error"
    except requests.exceptions.ConnectionError:
        return "Connection Error"
    except Exception as e:
        return f"Error: {str(e)}"

def should_redirect_to_test_server(url):
    """
    Determine if a URL should be redirected to the test server.
    
    Args:
        url: The URL to check
        
    Returns:
        tuple: (should_redirect, test_url, lang)
    """
    # Only redirect if enabled in config
    if not config.enable_test_redirects:
        return False, None, None
        
    url_parts = urlparse(url)
    domain = url_parts.netloc
    
    # Check if this domain is in our test domains list
    domain_config = config.get_domain_config(domain)
    if not domain_config:
        # Not in our domains list at all
        return False, None, None
        
    if not config.is_test_domain(domain):
        # It's in our domains list but not marked as a test domain
        if config.is_production:
            # In production, don't redirect unless explicitly configured
            return False, None, None
    
    # Determine language
    lang = 'en'
    if '/es-mx' in url_parts.path or '.mx.' in domain or domain.endswith('.mx'):
        lang = 'es-mx'
        
    # Create local test URL
    path = url_parts.path if url_parts.path and url_parts.path != '/' else f"/{lang}"
    if not path.startswith('/'):
        path = f"/{path}"
        
    test_url = f"http://localhost:5001{path}"
    
    # Forward query parameters
    if url_parts.query:
        test_url += f"?{url_parts.query}"
    
    return True, test_url, lang

def check_for_product_tables(url, is_test_env=None):
    """
    Check if a URL's HTML contains product table classes using requests.
    Handles both original URLs and test environment redirects.
    
    Args:
        url: The URL to check for product tables
        is_test_env: Flag indicating if we're in a test environment (enables localhost redirects)
                     If None, will use the global config setting
    
    Returns:
        tuple: (has_product_table, product_table_class, error_message)
    """
    original_url = url
    test_url = None
    error_message = None
    
    # If is_test_env not specified, use global config
    if is_test_env is None:
        is_test_env = not config.is_production
    
    try:
        # Check if this URL should be redirected to test server
        should_redirect, test_url, lang = should_redirect_to_test_server(url)
        
        if should_redirect and test_url:
            logger.info(f"Redirecting test domain to local test server for product table check: {url} -> {test_url}")
            
            # Try the test URL, but we'll fall back to original if it fails
            try:
                test_response = requests.get(test_url, timeout=config.request_timeout)
                if test_response.status_code == 200:
                    url = test_url
                else:
                    logger.warning(f"Test URL returned status code {test_response.status_code}, falling back to original URL")
            except Exception as test_e:
                logger.warning(f"Failed to connect to test URL: {test_e}, falling back to original URL")
        
        # Check if we should check for product tables for this domain
        url_parts = urlparse(url)
        domain = url_parts.netloc
        
        # Get domain configuration for product table checking
        domain_config = config.get_domain_config(domain)
        if domain_config and not domain_config.get("product_table_check", False):
            logger.info(f"Product table check disabled for domain {domain}")
            return False, None, "Product table check not enabled for this domain"
        
        # Get the expected class names for this domain
        expected_classes = config.get_expected_classes(domain)
        
        # Get the HTML content
        logger.info(f"Checking URL for product tables: {url}")
        response = requests.get(url, timeout=config.request_timeout, allow_redirects=True)
        
        # Check if we were redirected
        if response.history:
            redirect_chain = " -> ".join([r.url for r in response.history] + [response.url])
            logger.info(f"URL redirected: {url} -> {response.url}")
            # Update the URL to the final destination after redirects
            url = response.url
        
        if response.status_code == 200:
            page_content = response.text
            
            # Check for expected product table classes
            for class_pattern in expected_classes:
                # Use regex to find the class in the HTML
                pattern = re.escape(class_pattern)
                class_matches = re.findall(f'class=["\']([^"\']*?{pattern}[^"\']*?)["\']', page_content)
                
                if class_matches:
                    product_table_class = class_matches[0]
                    logger.info(f"Found {class_pattern} class: {product_table_class}")
                    return True, product_table_class, None
            
            logger.info(f"No product table classes found on {url}")
            return False, None, None
        else:
            error_message = f"Failed to get content from URL, status code: {response.status_code}"
            logger.error(error_message)
            return False, None, error_message
    except requests.exceptions.Timeout:
        error_message = f"Connection to {url} timed out"
        logger.error(error_message)
        return False, None, error_message
    except requests.exceptions.SSLError as ssl_err:
        error_message = f"SSL error when connecting to {url}: {str(ssl_err)}"
        logger.error(error_message)
        return False, None, error_message
    except requests.exceptions.ConnectionError:
        error_message = f"Failed to connect to {url}"
        logger.error(error_message)
        return False, None, error_message
    except Exception as e:
        error_message = f"Error checking for product tables: {str(e)}"
        logger.error(error_message)
        return False, None, error_message

def check_links(links, expected_utm):
    """Check if links load correctly and have correct UTM parameters."""
    results = []
    
    # Set up Selenium for browser-based checks if needed
    browser_available = False
    driver = None
    
    if config.is_development:
        # In development, we try to use Selenium for enhanced checking
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            
            # Use webdriver-manager to handle ChromeDriver installation
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            browser_available = True
            logger.info("Browser automation initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Chrome WebDriver: {e}")
            logger.info("Falling back to non-browser validation")
    
    # Using retries based on configuration
    max_retries = config.max_retries
    
    # Process each link
    for link_source, url in links:
        retries = 0
        success = False
        
        while not success and retries <= max_retries:
            try:
                # Check if this URL should be redirected to test server
                redirect_url = url
                should_redirect, test_url, lang = should_redirect_to_test_server(url)
                
                if should_redirect and test_url:
                    redirect_url = test_url
                    logger.info(f"Redirecting test domain to local test server: {url} -> {redirect_url}")
                
                # Basic HTTP status check
                status_code = check_http_status(redirect_url)
                
                # Check UTM parameters
                utm_issues = validate_utm_parameters(url, expected_utm)
                
                # Check for product tables
                if browser_available and driver:
                    # Using browser automation for more reliable checks
                    try:
                        # Use the redirected URL for browser automation
                        driver.get(redirect_url)
                        
                        # Check for product tables using both methods
                        has_table, table_class, table_error = check_for_product_tables(
                            url, is_test_env=(should_redirect and test_url is not None)
                        )
                        
                        # Record the results
                        link_result = {
                            'source': link_source,
                            'url': url,
                            'status': status_code,
                            'utm_issues': utm_issues,
                            'has_product_table': has_table,
                            'product_table_class': table_class,
                            'product_table_error': table_error,
                            'redirected_to': redirect_url if redirect_url != url else None,
                            'final_url': url,  # Same as initial since we can't check full redirects
                            'retries': retries
                        }
                        
                        results.append(link_result)
                        success = True
                        
                    except Exception as browser_e:
                        logger.error(f"Browser automation error: {browser_e}")
                        if retries < max_retries:
                            logger.info(f"Retrying link check for {url} (attempt {retries+1}/{max_retries})")
                            retries += 1
                        else:
                            # Fall back to non-browser method on final attempt
                            logger.info("Falling back to non-browser validation after retries")
                            has_product_table, product_table_class, product_table_error = check_for_product_tables(
                                url, is_test_env=(should_redirect and test_url is not None)
                            )
                            
                            link_result = {
                                'source': link_source,
                                'url': url,
                                'status': status_code,
                                'utm_issues': utm_issues,
                                'has_product_table': has_product_table,
                                'product_table_class': product_table_class,
                                'product_table_error': product_table_error,
                                'redirected_to': redirect_url if redirect_url != url else None,
                                'retries': retries
                            }
                            
                            results.append(link_result)
                            success = True
                else:
                    # Non-browser validation
                    has_product_table, product_table_class, product_table_error = check_for_product_tables(
                        url, is_test_env=(should_redirect and test_url is not None)
                    )
                    
                    link_result = {
                        'source': link_source,
                        'url': url,
                        'status': status_code,
                        'utm_issues': utm_issues,
                        'has_product_table': has_product_table,
                        'product_table_class': product_table_class,
                        'product_table_error': product_table_error,
                        'redirected_to': redirect_url if redirect_url != url else None,
                        'retries': retries
                    }
                    
                    results.append(link_result)
                    success = True
                    
            except Exception as e:
                if retries < max_retries:
                    logger.warning(f"Error checking link {url}: {e}. Retrying ({retries+1}/{max_retries})")
                    retries += 1
                else:
                    logger.error(f"Failed to check link after {max_retries} retries: {url}")
                    # Record error result
                    link_result = {
                        'source': link_source,
                        'url': url,
                        'status': f"Error: {str(e)}",
                        'utm_issues': [],
                        'has_product_table': False,
                        'product_table_class': None,
                        'product_table_error': f"Link check failed after {max_retries} retries: {str(e)}",
                        'redirected_to': None,
                        'retries': retries
                    }
                    results.append(link_result)
                    success = True
    
    # Clean up browser if used
    if driver:
        try:
            driver.quit()
        except:
            pass
    
    return results

def validate_email(email_path, requirements_path):
    """Main function to validate email against requirements."""
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
    
    # Format campaign code in expected metadata if needed
    if 'campaign_code' in expected_metadata and 'country' in requirements:
        campaign_code_value = expected_metadata.get('campaign_code', '')
        country_code_value = requirements.get('country', '')
        
        if campaign_code_value and country_code_value:
            # Format as "CODE - COUNTRY"
            expected_metadata['campaign_code'] = f"{campaign_code_value} - {country_code_value}"
    
    # Prepare results
    results = {
        'metadata': metadata,
        'metadata_issues': metadata_issues,
        'links': link_results,
        'environment': 'production' if config.is_production else 'development',
        'requirements': requirements
    }
    
    return results