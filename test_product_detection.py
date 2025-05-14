import re
import requests
from urllib.parse import urlparse

URL = "https://partly-products-showcase.lovable.app/products"

# Fetch the page content
print(f"Fetching content from {URL}...")
response = requests.get(URL, timeout=10)
page_content = response.text

print(f"Response status: {response.status_code}")
print(f"Content length: {len(page_content)} characters")

# Save a sample of the content
sample = page_content[:1000]
print(f"Content sample: {sample}")

# Define our patterns
product_class_patterns = [
    # Standard product table class
    r'class=["\']([^"\']*?product-table[^"\']*?)["\']',
    # Product list container
    r'class=["\']([^"\']*?productListContainer[^"\']*?)["\']',
    # Embedded styles with product-table
    r'\.product-table\s*\{',
    r'\.product[_\-\s]table\s*\{',
    r'\.product[_\-\s]list\s*\{',
    r'\.product[_\-\s]grid\s*\{',
    r'\.productTable\s*\{',
    r'\.productList\s*\{',
    # Table with product columns - based on screenshot
    r'Product\s*Name</th>',
    r'Product\s*(?:Name|Item|Number|ID)</th>',
    r'Part\s*Number</th>',
    r'Product\s*Inventory',
    r'Product\s*Details',
    r'Product\s*Catalog',
    r'Price</th>',
    r'Manufacturer</th>',
    r'Quantity\s*Available</th>',
    # React-specific patterns (often uses className instead of class)
    r'className=["\']([^"\']*?product[^"\']*?)["\']',
    r'className=["\']([^"\']*?item[_\-\s]list[^"\']*?)["\']',
    r'className=["\']([^"\']*?inventory[^"\']*?)["\']',
    r'className=["\']([^"\']*?catalog[^"\']*?)["\']',
    r'className=["\']table[^"\']*?["\']',
    # JSX/React component names
    r'<ProductTable',
    r'<ProductList',
    r'<ProductGrid',
    r'<ProductInventory',
    r'<ProductCatalog',
    # Product descriptions - based on screenshot
    r'>Digital Pressure Sensor<',
    r'>High-Pressure Hydraulic Valve<',
    r'>Industrial Ethernet Switch<',
    r'>Industrial Grade Bearing<',
    r'>Linear Actuator<',
    # More flexible patterns
    r'class=["\']([^"\']*?product[_\-\s]list[^"\']*?)["\']',
    r'class=["\']([^"\']*?product[_\-\s]grid[^"\']*?)["\']',
    r'class=["\']([^"\']*?products[_\-\s]container[^"\']*?)["\']',
    r'class=["\']([^"\']*?product[_\-\s]inventory[^"\']*?)["\']',
    # Common eCommerce specific patterns
    r'class=["\']([^"\']*?product[_\-\s]catalog[^"\']*?)["\']',
    r'class=["\']([^"\']*?shop[_\-\s]products[^"\']*?)["\']',
    r'class=["\']([^"\']*?product[_\-\s]showcase[^"\']*?)["\']',
    # Generic product-related patterns
    r'class=["\']([^"\']*?product(?:s|)[^"\']*?)["\']',
    r'class=["\']([^"\']*?catalog[_\-\s](?:item|product)[^"\']*?)["\']',
    # Common div id patterns
    r'id=["\']products["\']',
    r'id=["\']product-list["\']',
    r'id=["\']product-grid["\']',
    r'id=["\']product-inventory["\']'
]

# Check each pattern
print(f"Checking {len(product_class_patterns)} patterns for product tables...")
found_patterns = 0

for pattern in product_class_patterns:
    match = re.search(pattern, page_content)
    if match:
        found_patterns += 1
        print(f"\n✓ MATCH FOUND! Pattern: '{pattern}'")
        print(f"Matched text: '{match.group(0)}'")
        try:
            # Try to get the captured group if available
            group = match.group(1)
            print(f"Captured group: '{group}'")
        except IndexError:
            print("No capture group in this pattern")

print(f"\nSummary: Found {found_patterns} matching patterns out of {len(product_class_patterns)}")
if found_patterns == 0:
    print("No product table detected!")