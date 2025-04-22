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
    
    return {
        'sender': sender.get('content') or (sender.get_text(strip=True) if hasattr(sender, 'get_text') else '') or 'Not found',
        'sender_name': sender_name.get('content') or (sender_name.get_text(strip=True) if hasattr(sender_name, 'get_text') else '') or 'Not found',
        'reply_to': reply_to.get('content') or (reply_to.get_text(strip=True) if hasattr(reply_to, 'get_text') else '') or 'Not found',
        'subject': subject.get('content') or (subject.get_text(strip=True) if hasattr(subject, 'get_text') else '') or 'Not found',
        'preheader': preheader_text,
        'preheader_details': f"Attempted classes: {', '.join(attempted_classes)}" if not hasattr(preheader, 'get_text') else ''
    }

def extract_links(soup):
    """Extract all links from email HTML with enhanced source context."""
    links = []
    for a in soup.find_all('a', href=True):
        # Check if this link contains an image
        img = a.find('img')
        if img:
            # This is an image link - extract image info
            alt_text = img.get('alt', '').strip() or 'Image link'
            src = img.get('src', '')
            width = img.get('width', '100')
            height = img.get('height', 'auto')
            
            # Create a visual representation using img tag
            link_source = {
                'type': 'image',
                'text': alt_text,
                'image_src': src,
                'image_alt': alt_text,
                'image_width': width,
                'image_height': height
            }
        else:
            # Regular text link
            link_source = {
                'type': 'text',
                'text': a.get_text(strip=True) or 'Empty link text'
            }
        
        # Store the link with its source context
        links.append((link_source, a['href']))
    
    return links

def validate_utm_parameters(url, expected_utm):
    """Validate UTM parameters in a URL against expected values."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    discrepancies = []
    
    for key, expected_value in expected_utm.items():
        actual_value = params.get(key, [None])[0]
        if actual_value != expected_value:
            discrepancies.append(f"UTM {key}: Expected '{expected_value}', got '{actual_value}'")
    
    return discrepancies

def check_http_status(url):
    """Check HTTP status code of a URL."""
    try:
        # Handle local test domains
        if 'localtest.me' in url:
            # Replace with local test server for *.localtest.me domains
            url_parts = urlparse(url)
            domain = url_parts.netloc
            
            # Extract language info from domain
            lang = 'es-mx' if '.mx.' in domain or domain.endswith('.mx') else 'en'
            
            # Create local test URL
            path = url_parts.path if url_parts.path else f"/{lang}"
            if not path.startswith('/'):
                path = f"/{path}"
                
            test_url = f"http://localhost:5001{path}"
            
            # Forward query parameters
            if url_parts.query:
                test_url += f"?{url_parts.query}"
                
            logger.info(f"Redirecting remote URL to local test server: {url} -> {test_url}")
            response = requests.head(test_url, timeout=5, allow_redirects=True)
        else:
            response = requests.head(url, timeout=5, allow_redirects=True)
            
        return response.status_code
    except Exception as e:
        logger.error(f"Failed to check HTTP status: {e}")
        return None

def check_links(links, expected_utm):
    """Check if links load correctly and have correct UTM parameters."""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    
    try:
        # Use webdriver-manager to handle ChromeDriver installation
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except Exception as e:
        logger.error(f"Failed to initialize Chrome WebDriver: {e}")
        # Fallback - validate UTM parameters without browser automation
        results = []
        for link_source, url in links:
            try:
                # Process URL for localtest.me domains
                redirect_url = url
                if 'localtest.me' in url:
                    url_parts = urlparse(url)
                    domain = url_parts.netloc
                    
                    # Extract language info
                    lang = 'es-mx' if '.mx.' in domain or domain.endswith('.mx') else 'en'
                    
                    # Create local test URL
                    path = url_parts.path if url_parts.path and url_parts.path != '/' else f"/{lang}"
                    if not path.startswith('/'):
                        path = f"/{path}"
                    
                    test_url = f"http://localhost:5001{path}"
                    
                    # Forward query parameters
                    if url_parts.query:
                        test_url += f"?{url_parts.query}"
                    
                    redirect_url = test_url
                    logger.info(f"Redirecting domain to local test server: {url} -> {redirect_url}")
                
                # Just validate the UTM parameters in the initial URL
                discrepancies = validate_utm_parameters(url, expected_utm)
                
                # Check HTTP status code
                http_status = check_http_status(url)
                
                # Determine status based on UTM parameters and HTTP status
                if http_status in [200, 301, 302]:
                    status = 'PASS' if not discrepancies else 'FAIL'
                else:
                    status = 'FAIL'
                    if http_status:
                        discrepancies.append(f"HTTP status code: {http_status}")
                    else:
                        discrepancies.append("Unable to connect to URL")
                
                # Format the link data for frontend display
                is_image_link = link_source.get('type') == 'image'
                link_entry = {
                    'link_text': link_source.get('text', 'No text'),
                    'is_image_link': is_image_link,
                    'url': url,
                    'redirected_to': redirect_url if redirect_url != url else None,
                    'final_url': url,  # Same as initial since we can't check redirects
                    'status': status,
                    'http_status': http_status,
                    'utm_issues': discrepancies or ["Browser automation unavailable - basic URL check only"]
                }
                
                # Add image properties if this is an image link
                if is_image_link:
                    link_entry['image_src'] = link_source.get('image_src', '')
                    link_entry['image_alt'] = link_source.get('image_alt', '')
                
                results.append(link_entry)
            except Exception as link_error:
                # Format the link data for frontend display even in error cases
                is_image_link = link_source.get('type') == 'image'
                link_entry = {
                    'link_text': link_source.get('text', 'No text'),
                    'is_image_link': is_image_link,
                    'url': url,
                    'redirected_to': None,
                    'final_url': None,
                    'status': 'ERROR',
                    'http_status': None,
                    'utm_issues': [f"Failed to analyze URL: {str(link_error)}"]
                }
                
                # Add image properties if this is an image link
                if is_image_link:
                    link_entry['image_src'] = link_source.get('image_src', '')
                    link_entry['image_alt'] = link_source.get('image_alt', '')
                
                results.append(link_entry)
        
        return results
    
    results = []
    
    for link_source, url in links:
        try:
            # Process URL for localtest.me domains
            redirect_url = url
            if 'localtest.me' in url:
                url_parts = urlparse(url)
                domain = url_parts.netloc
                
                # Extract language info
                lang = 'es-mx' if '.mx.' in domain or domain.endswith('.mx') else 'en'
                
                # Create local test URL
                path = url_parts.path if url_parts.path and url_parts.path != '/' else f"/{lang}"
                if not path.startswith('/'):
                    path = f"/{path}"
                
                test_url = f"http://localhost:5001{path}"
                
                # Forward query parameters
                if url_parts.query:
                    test_url += f"?{url_parts.query}"
                
                redirect_url = test_url
                logger.info(f"Redirecting domain to local test server: {url} -> {redirect_url}")
            
            # Check HTTP status code first
            http_status = check_http_status(url)
            
            # Continue with Selenium for detailed UTM analysis
            # Use the redirected URL for browser automation
            driver.get(redirect_url)
            final_url = driver.current_url
            
            # For local testing, validate original URL's parameters
            utm_discrepancies = validate_utm_parameters(url, expected_utm)
            
            # Special handling for webtrends parameter - null/empty is OK
            utm_discrepancies = [d for d in utm_discrepancies if not (d.startswith('UTM webtrends') and ('got \'None\'' in d or 'got \'\'' in d))]
            
            # Determine overall status
            if http_status in [200, 301, 302]:
                status = 'PASS' if not utm_discrepancies else 'FAIL'
            else:
                status = 'FAIL'
                if http_status:
                    utm_discrepancies.append(f"HTTP Error: Status code {http_status}")
            
            # Get the display text based on link type
            display_text = link_source['text'] if isinstance(link_source, dict) and 'text' in link_source else str(link_source)
            
            # Format the link data for frontend display
            is_image_link = link_source.get('type') == 'image'
            link_entry = {
                'link_text': link_source.get('text', 'No text'),
                'is_image_link': is_image_link,
                'url': url,
                'redirected_to': redirect_url if redirect_url != url else None,
                'final_url': final_url,
                'status': status,
                'http_status': http_status,
                'utm_issues': utm_discrepancies
            }
            
            # Add image properties if this is an image link
            if is_image_link:
                link_entry['image_src'] = link_source.get('image_src', '')
                link_entry['image_alt'] = link_source.get('image_alt', '')
            
            results.append(link_entry)
            logger.info(f"Checked link '{display_text}': {status} (HTTP: {http_status})")
        except Exception as e:
            http_status = check_http_status(url) 
            # Format the link data for frontend display even in error cases
            is_image_link = link_source.get('type') == 'image'
            link_entry = {
                'link_text': link_source.get('text', 'No text'),
                'is_image_link': is_image_link,
                'url': url,
                'redirected_to': None,
                'final_url': None,
                'status': 'FAIL',
                'http_status': http_status,
                'utm_issues': [f"Failed to load: {str(e)}"]
            }
            
            # Add image properties if this is an image link
            if is_image_link:
                link_entry['image_src'] = link_source.get('image_src', '')
                link_entry['image_alt'] = link_source.get('image_alt', '')
            
            results.append(link_entry)
            logger.error(f"Error checking link: {e}")
    
    driver.quit()
    return results

def validate_email(email_path, requirements_path):
    """Main function to validate email against requirements."""
    requirements = load_requirements(requirements_path)
    soup = parse_email_html(email_path)
    
    metadata = extract_email_metadata(soup)
    results = {'metadata': [], 'links': []}
    
    # Field mapping between metadata and requirements
    field_mapping = {
        'sender': ['sender', 'sender_address'],  # Try both variants
        'sender_name': ['sender_name'],
        'reply_to': ['reply_to', 'reply_address'],  # Try both variants
        'subject': ['subject'],
        'preheader': ['preheader']
    }
    
    # Fields to validate
    fields_to_check = ['sender', 'sender_name', 'reply_to', 'subject', 'preheader']
    
    for key in fields_to_check:
        if key in metadata:
            actual = metadata[key]
            
            # Try multiple possible keys in requirements
            expected = 'Not specified'
            for req_key in field_mapping[key]:
                if req_key in requirements:
                    expected = requirements[req_key]
                    break
            
            # Special comparison for preheader - if we have extracted just the visible part,
            # check if it's at the beginning of the expected text
            if key == 'preheader' and actual != 'Not found' and expected != 'Not specified':
                # Check if the actual preheader is a prefix of the expected preheader
                # or if the expected preheader is a prefix of the actual preheader
                if actual.startswith(expected) or expected.startswith(actual):
                    status = 'PASS'
                else:
                    status = 'FAIL'
            else:
                status = 'PASS' if actual == expected else 'FAIL'
            
            result_item = {
                'field': key,
                'expected': expected,
                'actual': actual,
                'status': status
            }
            
            # Add additional details for preheader if available
            if key == 'preheader' and status == 'FAIL' and metadata.get('preheader_details'):
                result_item['details'] = metadata['preheader_details']
            
            results['metadata'].append(result_item)
            logger.info(f"Validated {key}: {status}")
    
    links = extract_links(soup)
    if links:
        link_results = check_links(links, requirements.get('utm_parameters', {}))
        results['links'] = link_results
    
    return results
