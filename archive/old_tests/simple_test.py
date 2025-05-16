import requests
import os

def test_basic_app_functionality():
    """Test the basic functionality of the Email QA application."""
    
    # 1. Check that the main page loads
    print("Testing main page...")
    response = requests.get("http://localhost:5000/")
    if response.status_code == 200:
        print(f"✓ Main page loaded successfully (status code: {response.status_code})")
        if "Email QA Automation" in response.text:
            print("✓ Found expected content on the main page")
        else:
            print("✗ Did not find expected content on the main page")
    else:
        print(f"✗ Failed to load main page (status code: {response.status_code})")
        return False
    
    # 2. Test API endpoint with sample files
    print("\nTesting API endpoint with sample files...")
    email_file = os.path.join("attached_assets", "Replit_test_email.html")
    requirements_file = os.path.join("attached_assets", "sample_requirements.json")
    
    if not os.path.exists(email_file):
        print(f"✗ Test email file not found: {email_file}")
        return False
        
    if not os.path.exists(requirements_file):
        print(f"✗ Requirements file not found: {requirements_file}")
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
    
    # Make the API request
    try:
        response = requests.post(
            "http://localhost:5000/run-qa",
            files=files,
            headers=headers
        )
        
        # Check response
        if response.status_code == 200:
            print(f"✓ API call succeeded (status code: {response.status_code})")
            
            # Verify response headers
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                print(f"✓ Content-Type is correct: {content_type}")
            else:
                print(f"✗ Content-Type is incorrect: {content_type}")
            
            # Verify JSON parsing
            try:
                data = response.json()
                print("✓ Response parsed as valid JSON")
                
                # Check for expected data
                if 'metadata' in data and 'links' in data:
                    print(f"✓ Response contains expected keys: metadata ({len(data['metadata'])} items) and links ({len(data['links'])} items)")
                    
                    # Check for campaign code validation
                    campaign_code_result = next((item for item in data['metadata'] if item.get('field') == 'footer_campaign_code'), None)
                    if campaign_code_result:
                        print(f"✓ Campaign code validation: {campaign_code_result.get('status', 'UNKNOWN')}")
                        print(f"  - Expected: {campaign_code_result.get('expected', 'N/A')}")
                        print(f"  - Actual: {campaign_code_result.get('actual', 'N/A')}")
                    else:
                        print("✗ Campaign code validation result not found")
                    
                    # Sample data from the response
                    print("\nSample metadata field:")
                    if data['metadata']:
                        print(f"  {data['metadata'][0]}")
                        
                    print("\nSample link data:")
                    if data['links']:
                        first_link = data['links'][0]
                        link_info = {
                            'link_text': first_link.get('link_text', 'N/A'),
                            'url': first_link.get('url', 'N/A'),
                            'status': first_link.get('status', 'N/A'),
                            'utm_issues': first_link.get('utm_issues', [])
                        }
                        print(f"  {link_info}")
                else:
                    print("✗ Response is missing expected keys (metadata and/or links)")
                    
            except ValueError as e:
                print(f"✗ Failed to parse response as JSON: {e}")
                print(f"Response text begins with: {response.text[:100]}...")
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
    test_basic_app_functionality()