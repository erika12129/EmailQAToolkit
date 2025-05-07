import requests
import json
import os

def test_product_table_detection():
    """Test the product table class detection in destination pages."""
    
    print("Testing product table class detection...")
    
    # Use English email sample
    email_file = os.path.join("attached_assets", "Replit_test_email.html")
    requirements_file = os.path.join("attached_assets", "sample_requirements.json")
    
    if not os.path.exists(email_file) or not os.path.exists(requirements_file):
        print("✗ Test files not found")
        return False
    
    # Prepare files for upload
    files = {
        'email': open(email_file, 'rb'),
        'requirements': open(requirements_file, 'rb')
    }
    
    # Set headers
    headers = {
        'Accept': 'application/json'
    }
    
    try:
        # Make the API request
        response = requests.post(
            "http://localhost:5000/run-qa",
            files=files,
            headers=headers
        )
        
        # Check response
        if response.status_code == 200:
            print(f"✓ API call succeeded (status code: {response.status_code})")
            
            try:
                # Parse JSON response
                data = response.json()
                print("✓ Response parsed as valid JSON")
                
                # Check links array
                if 'links' in data and data['links']:
                    # Check all links for product table detection
                    product_links = [link for link in data['links'] 
                                    if 'products' in link.get('url', '').lower()]
                    
                    if product_links:
                        print(f"✓ Found {len(product_links)} product links to analyze")
                        
                        for i, link in enumerate(product_links):
                            print(f"\nLink {i+1}: {link.get('url')}")
                            
                            # Check for product table presence
                            has_table = link.get('has_product_table', False)
                            print(f"  Has product table: {has_table}")
                            
                            if has_table:
                                print(f"  Product table class: {link.get('product_table_class')}")
                            elif 'product_table_error' in link:
                                print(f"  Error: {link.get('product_table_error')}")
                    else:
                        print("✗ No product links found in the email")
                else:
                    print("✗ No links found in API response")
            
            except ValueError as e:
                print(f"✗ Failed to parse response as JSON: {e}")
        else:
            print(f"✗ API call failed (status code: {response.status_code})")
            print(f"Response: {response.text[:100]}...")
    
    except Exception as e:
        print(f"✗ Error during API test: {e}")
    
    finally:
        # Clean up
        for file in files.values():
            file.close()
    
    print("\nTest completed!")
    return True

if __name__ == "__main__":
    test_product_table_detection()