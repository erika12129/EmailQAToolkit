import json
import re
import os
import logging
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
    """Extract sender, subject, and preheader from email HTML."""
    sender = soup.find('meta', {'name': 'sender'}) or soup.find('from') or {}
    subject = soup.find('meta', {'name': 'subject'}) or soup.find('title') or {}
    preheader = soup.find('div', {'class': 'preheader'}) or soup.find('span', {'class': 'preheader'}) or {}
    
    return {
        'sender': sender.get('content') or (sender.get_text(strip=True) if hasattr(sender, 'get_text') else '') or 'Not found',
        'subject': subject.get('content') or (subject.get_text(strip=True) if hasattr(subject, 'get_text') else '') or 'Not found',
        'preheader': preheader.get_text(strip=True) if hasattr(preheader, 'get_text') else 'Not found'
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
        # Fallback - returning results without checking URLs
        return [
            {
                'link_text': text,
                'url': url,
                'final_url': None,
                'status': 'ERROR',
                'utm_issues': [f"Browser automation unavailable: {str(e)}"]
            } for text, url in links
        ]
    
    results = []
    
    for text, url in links:
        try:
            driver.get(url)
            final_url = driver.current_url
            utm_discrepancies = validate_utm_parameters(final_url, expected_utm)
            status = 'PASS' if not utm_discrepancies else 'FAIL'
            results.append({
                'link_text': text,
                'url': url,
                'final_url': final_url,
                'status': status,
                'utm_issues': utm_discrepancies
            })
            logger.info(f"Checked link '{text}': {status}")
        except Exception as e:
            results.append({
                'link_text': text,
                'url': url,
                'final_url': None,
                'status': 'FAIL',
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
    
    for key in ['sender', 'subject', 'preheader']:
        actual = metadata[key]
        expected = requirements.get(key, 'Not specified')
        status = 'PASS' if actual == expected else 'FAIL'
        results['metadata'].append({
            'field': key,
            'expected': expected,
            'actual': actual,
            'status': status
        })
        logger.info(f"Validated {key}: {status}")
    
    links = extract_links(soup)
    if links:
        link_results = check_links(links, requirements.get('utm_parameters', {}))
        results['links'] = link_results
    
    return results
