"""
Test script for our improved text-based product detection strategy.
This tests various URLs to see if our detection logic correctly identifies product pages.
"""

import logging
import json
from web_scraper import check_for_product_tables_with_text_analysis

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# URLs to test
URLS = [
    "https://partly-products-showcase.lovable.app/products",  # Main products page
    "https://partly-products-showcase.lovable.app/",          # Homepage
    "https://example.com"                                      # Control site with no products
]

def main():
    """Run tests on improved text-based product detection."""
    logger.info("Testing improved text-based product detection...")
    
    results = {}
    for url in URLS:
        logger.info(f"Testing URL: {url}")
        result = check_for_product_tables_with_text_analysis(url)
        logger.info(f"Detection result for {url}: {result}")
        results[url] = result
    
    # Print summary
    logger.info("Summary of detection results:")
    for url, result in results.items():
        detection_status = "✓ Detected products" if result.get('found') else "✗ No products detected"
        confidence = result.get('confidence', 'N/A')
        method = result.get('detection_method', 'N/A')
        
        logger.info(f"{url}: {detection_status} (Confidence: {confidence}, Method: {method})")
    
    return results

if __name__ == "__main__":
    results = main()
    
    # Pretty print final results
    print("\nDetailed Results:")
    print(json.dumps(results, indent=2))