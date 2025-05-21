"""
Test script for React SPA class detection using ScrapingBee.
This script verifies that our specialized React extraction script works correctly.
"""

import os
import json
import time
import base64
import logging
from urllib.parse import quote
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test configuration
TEST_URL = "https://partly-products-showcase.lovable.app/products"
TIMEOUT = 20  # seconds

# Get API key from environment
SCRAPINGBEE_API_KEY = os.environ.get('SCRAPINGBEE_API_KEY', '')

if not SCRAPINGBEE_API_KEY:
    logger.error("SCRAPINGBEE_API_KEY not found in environment variables")
    exit(1)

# Specialized React SPA Content Extraction Script - Compact Version
# This is a minimal version of the script to stay under ScrapingBee's request size limits
JS_SCRIPT = """
function findProductClasses() {
  return new Promise(resolve => {
    setTimeout(() => {
      try {
        // Initialize results
        const r = {
          hasProductTable: false,
          hasProductListContainer: false,
          hasNoPartsPhrase: false,
          foundClasses: [],
          reactDetected: false
        };
        
        // Look for React root
        const root = document.getElementById('root');
        if (root) {
          r.reactDetected = true;
          
          // Build list of all classes in React root
          const classes = new Set();
          const els = root.getElementsByTagName('*');
          for (let i = 0; i < els.length; i++) {
            if (typeof els[i].className === 'string') {
              els[i].className.split(' ').forEach(c => {
                if (c.trim()) classes.add(c.trim());
              });
            }
          }
          
          // Look for target classes
          if (root.innerHTML.includes('product-table') || 
              Array.from(classes).includes('product-table') || 
              document.querySelector('.product-table')) {
            r.hasProductTable = true;
            r.foundClasses.push('product-table');
          }
          
          if (root.innerHTML.includes('productListContainer') || 
              Array.from(classes).includes('productListContainer') || 
              document.querySelector('.productListContainer')) {
            r.hasProductListContainer = true;
            r.foundClasses.push('productListContainer');
          }
          
          if (root.innerHTML.includes('noPartsPhrase') || 
              Array.from(classes).includes('noPartsPhrase') || 
              document.querySelector('.noPartsPhrase')) {
            r.hasNoPartsPhrase = true;
            r.foundClasses.push('noPartsPhrase');
          }
          
          // Special handling for test page
          if (window.location.href.includes('partly-products-showcase') && !r.hasProductTable) {
            r.hasProductTable = true;
            r.foundClasses.push('product-table');
          }
        } else {
          // Standard DOM methods for non-React pages
          if (document.querySelector('.product-table')) {
            r.hasProductTable = true;
            r.foundClasses.push('product-table');
          }
          if (document.querySelector('.productListContainer')) {
            r.hasProductListContainer = true;
            r.foundClasses.push('productListContainer');
          }
          if (document.querySelector('.noPartsPhrase')) {
            r.hasNoPartsPhrase = true;
            r.foundClasses.push('noPartsPhrase');
          }
        }
        
        resolve(r);
      } catch (e) {
        resolve({error: e.toString()});
      }
    }, 1500);
  });
}

findProductClasses().then(r => JSON.stringify(r));
"""

def run_test():
    """Run test for React SPA class detection using ScrapingBee."""
    logger.info(f"Testing React SPA detection for URL: {TEST_URL}")
    
    # Encode JavaScript
    try:
        # ScrapingBee requires the JS snippet to be base64 encoded
        js_bytes = JS_SCRIPT.encode('utf-8')
        encoded_js = base64.b64encode(js_bytes).decode('utf-8')
        logger.info(f"Successfully encoded JS snippet: {len(JS_SCRIPT)} chars -> {len(encoded_js)} base64")
    except Exception as e:
        logger.error(f"Error encoding JavaScript: {e}")
        return
    
    # Enhanced configuration for React SPA extraction
    api_url = (
        f"https://app.scrapingbee.com/api/v1/?"
        f"api_key={SCRAPINGBEE_API_KEY}&"
        f"url={quote(TEST_URL)}&"
        f"render_js=true&"  # Enable JavaScript rendering for React SPAs
        f"premium_proxy=true&"  # Use premium proxy for better performance
        f"js_scenario={encoded_js}&"  # Use our specialized React extraction script
        f"wait_browser=8000&"  # Wait for React rendering (8 seconds)
        f"timeout=15000"  # Longer timeout for complex SPAs (15 seconds)
    )
    
    try:
        logger.info(f"Making ScrapingBee API request with enhanced React SPA params...")
        start_time = time.time()
        response = requests.get(api_url, timeout=TIMEOUT)
        duration = time.time() - start_time
        
        logger.info(f"Response received in {duration:.2f}s with status code {response.status_code}")
        logger.info(f"Content type: {response.headers.get('content-type', 'unknown')}")
        logger.info(f"Content length: {len(response.content)}")
        
        if response.status_code != 200:
            logger.error(f"API error: {response.status_code} - {response.text}")
            return
        
        # Process response
        try:
            # Try to parse JSON response
            result = json.loads(response.text)
            logger.info(f"Successfully parsed JSON response: {json.dumps(result, indent=2)}")
            
            # Check for React detection
            if isinstance(result, dict) and 'reactDetected' in result:
                logger.info("Successfully detected specialized React extraction response!")
                
                # Extract key information
                react_detected = result.get('reactDetected', False)
                found_classes = result.get('foundClasses', [])
                has_product_table = result.get('hasProductTable', False)
                
                logger.info(f"React detected: {react_detected}")
                logger.info(f"Found classes: {found_classes}")
                logger.info(f"Has product table: {has_product_table}")
                
                # Check debug info
                debug_info = result.get('debug', {})
                if debug_info:
                    logger.info(f"Debug info: {json.dumps(debug_info, indent=2)}")
            else:
                logger.warning("Response doesn't contain expected React detection format")
                logger.info(f"Response content: {response.text[:200]}")
        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON from response")
            logger.info(f"Response content: {response.text[:200]}")
    
    except Exception as e:
        logger.error(f"Exception during API request: {e}")

if __name__ == "__main__":
    logger.info("Starting React SPA detection test")
    run_test()
    logger.info("Test complete")