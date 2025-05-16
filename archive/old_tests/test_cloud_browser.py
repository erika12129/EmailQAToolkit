"""
Quick test script to check if our cloud browser implementation is working.
This will use the same code as the main app but in a simpler context.
"""

import os
import base64
import requests
from urllib.parse import quote, quote_plus

# Setup test variables
SCRAPINGBEE_API_KEY = os.environ.get('SCRAPINGBEE_API_KEY', '')
test_url = "https://partly.com"  # A real e-commerce site that should have product tables

# Simple JS script that just returns document.title
js_script = """
return document.title;
"""

def main():
    """Run the ScrapingBee API test"""
    # Check if we have an API key
    if not SCRAPINGBEE_API_KEY:
        print("ERROR: No ScrapingBee API key found in environment variables")
        return
    
    print(f"API Key available: {bool(SCRAPINGBEE_API_KEY)}")
    print(f"API Key begins with: {SCRAPINGBEE_API_KEY[:4]}...")
    
    # Encode the JavaScript snippet properly
    try:
        # First base64 encode
        base64_js = base64.b64encode(js_script.encode('utf-8')).decode('utf-8')
        
        # Then URL-encode the base64 string for the API URL
        url_encoded_js = quote_plus(base64_js)
        
        print(f"Original JS: {js_script}")
        print(f"Base64 encoded: {base64_js}")
        print(f"URL encoded JS: {url_encoded_js}")
    except Exception as e:
        print(f"ERROR encoding JavaScript: {str(e)}")
        return
    
    # Prepare the test URL
    print(f"Testing with URL: {test_url}")
    url_encoded_url = quote_plus(test_url)
    print(f"URL encoded test URL: {url_encoded_url}")
    
    # Construct the full API URL (with reliable parameters)
    api_url = (
        f"https://app.scrapingbee.com/api/v1/?"
        f"api_key={SCRAPINGBEE_API_KEY}&"
        f"url={quote(test_url)}&"
        f"render_js=true&"
        f"js_snippet={url_encoded_js}&"
        f"timeout=10000&"
        f"premium_proxy=true"
    )
    
    print(f"Making request to ScrapingBee API...")
    try:
        # Make the API request with a shorter timeout to avoid tool timeout
        response = requests.get(api_url, timeout=10)
        
        # Print response information
        print(f"Response status code: {response.status_code}")
        print(f"Response content type: {response.headers.get('content-type', '')}")
        print(f"Response headers: {response.headers}")
        
        # Check if successful
        if response.status_code == 200:
            # Try to parse as JSON
            try:
                result = response.json()
                print(f"Successfully parsed response as JSON: {result}")
            except Exception as json_error:
                print(f"Could not parse response as JSON: {str(json_error)}")
                print(f"Response text: {response.text[:200]}...")
        else:
            print(f"Error response from ScrapingBee: {response.text[:200]}...")
        
    except Exception as e:
        print(f"Error making request: {str(e)}")

# Run the test
if __name__ == "__main__":
    main()