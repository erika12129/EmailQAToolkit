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
    sender = soup.find('meta', {'name': 'sender'}) or soup.find('from') or {}
    sender_name = soup.find('meta', {'name': 'sender-name'}) or soup.find('from-name') or {}
    reply_to = soup.find('meta', {'name': 'reply-to'}) or soup.find('reply-to') or {}
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
    
    return {
        'sender': sender.get('content') or (sender.get_text(strip=True) if hasattr(sender, 'get_text') else '') or 'Not found',
        'sender_name': sender_name.get('content') or (sender_name.get_text(strip=True) if hasattr(sender_name, 'get_text') else '') or 'Not found',
        'reply_to': reply_to.get('content') or (reply_to.get_text(strip=True) if hasattr(reply_to, 'get_text') else '') or 'Not found',
        'subject': subject.get('content') or (subject.get_text(strip=True) if hasattr(subject, 'get_text') else '') or 'Not found',
        'preheader': preheader.get_text(strip=True) if hasattr(preheader, 'get_text') else 'Not found',
        'preheader_details': f"Attempted classes: {', '.join(attempted_classes)}" if not hasattr(preheader, 'get_text') else ''
    }

def extract_links(soup):
    """Extract all links from email HTML."""
    return [(a.get_text(strip=True), a['href']) for a in soup.find_all('a', href=True)]

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
        for text, url in links:
            try:
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
                
                results.append({
                    'link_text': text,
                    'url': url,
                    'final_url': url,  # Same as initial since we can't check redirects
                    'status': status,
                    'http_status': http_status,
                    'utm_issues': discrepancies or ["Browser automation unavailable - basic URL check only"]
                })
            except Exception as link_error:
                results.append({
                    'link_text': text,
                    'url': url,
                    'final_url': None,
                    'status': 'ERROR',
                    'http_status': None,
                    'utm_issues': [f"Failed to analyze URL: {str(link_error)}"]
                })
        
        return results
    
    results = []
    
    for text, url in links:
        try:
            # Check HTTP status code first
            http_status = check_http_status(url)
            
            # Continue with Selenium for detailed UTM analysis
            driver.get(url)
            final_url = driver.current_url
            utm_discrepancies = validate_utm_parameters(final_url, expected_utm)
            
            # Special handling for webtrends parameter - empty is OK
            utm_discrepancies = [d for d in utm_discrepancies if not (d.startswith('UTM webtrends') and 'got \'None\'' in d)]
            
            # Determine overall status
            if http_status in [200, 301, 302]:
                status = 'PASS' if not utm_discrepancies else 'FAIL'
            else:
                status = 'FAIL'
                if http_status:
                    utm_discrepancies.append(f"HTTP Error: Status code {http_status}")
            
            results.append({
                'link_text': text,
                'url': url,
                'final_url': final_url,
                'status': status,
                'http_status': http_status,
                'utm_issues': utm_discrepancies
            })
            logger.info(f"Checked link '{text}': {status} (HTTP: {http_status})")
        except Exception as e:
            http_status = check_http_status(url) 
            results.append({
                'link_text': text,
                'url': url,
                'final_url': None,
                'status': 'FAIL',
                'http_status': http_status,
                'utm_issues': [f"Failed to load: {str(e)}"]
            })
            logger.error(f"Error checking link '{text}': {e}")
    
    driver.quit()
    return results

def validate_email(email_path, requirements_path):
    """Main function to validate email against requirements."""
    requirements = load_requirements(requirements_path)
    soup = parse_email_html(email_path)
    
    metadata = extract_email_metadata(soup)
    results = {'metadata': [], 'links': []}
    
    # Fields to validate
    fields_to_check = ['sender', 'sender_name', 'reply_to', 'subject', 'preheader']
    
    for key in fields_to_check:
        if key in metadata:
            actual = metadata[key]
            expected = requirements.get(key, 'Not specified')
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
