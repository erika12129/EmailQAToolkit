"""
Test script for checking product table detection on dynamic client-side rendered sites.
"""

import logging
from email_qa_enhanced import check_for_product_tables
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

def test_all_detection_methods():
    """
    Test all detection methods to see which ones correctly identify product tables.
    """
    print("\n===== Testing All Product Table Detection Methods =====")
    
    for url in URLS:
        print(f"\n\nTesting URL: {url}")
        print("=" * 60)
        
        # Test standard detection
        print("\n1. Standard detection (HTTP + fallbacks):")
        try:
            result = check_for_product_tables(url, timeout=10)
            print(f"Result: {result}")
            
            if result.get('found', False):
                print(f"✅ FOUND! Method: {result.get('detection_method', 'unknown')}")
                if 'class_name' in result:
                    print(f"Class name: {result.get('class_name')}")
                if 'confidence_score' in result:
                    print(f"Confidence: {result.get('confidence_score')}")
            else:
                print(f"❌ NOT FOUND. Method: {result.get('detection_method', 'unknown')}")
                if 'error' in result:
                    print(f"Error: {result.get('error')}")
        except Exception as e:
            print(f"Error during detection: {str(e)}")
        
        # Test text analysis directly
        print("\n2. Text analysis only:")
        try:
            text_result = check_for_product_tables_with_text_analysis(url)
            print(f"Result: {text_result}")
            
            if text_result.get('found', False):
                print(f"✅ FOUND! Confidence: {text_result.get('confidence_score', 0)}")
                if 'found_terms' in text_result:
                    print(f"Found terms: {text_result.get('found_terms', [])}")
            else:
                print(f"❌ NOT FOUND")
                if 'error' in text_result:
                    print(f"Error: {text_result.get('error')}")
        except Exception as e:
            print(f"Error during text analysis: {str(e)}")

if __name__ == "__main__":
    test_all_detection_methods()