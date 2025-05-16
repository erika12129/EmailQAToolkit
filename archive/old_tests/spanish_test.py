import requests
import os

def test_spanish_email():
    """Test the Email QA application with the Spanish email sample."""
    
    print("Testing API endpoint with Spanish email sample...")
    email_file = os.path.join("attached_assets", "Replit_test_es_MX.html")
    requirements_file = os.path.join("attached_assets", "sample_requirements_esMX.json")
    
    if not os.path.exists(email_file):
        print(f"✗ Spanish test email file not found: {email_file}")
        return False
        
    if not os.path.exists(requirements_file):
        print(f"✗ Spanish requirements file not found: {requirements_file}")
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
            
            # Verify JSON parsing
            try:
                data = response.json()
                print("✓ Response parsed as valid JSON")
                
                # Check for campaign code validation
                campaign_code_result = next((item for item in data['metadata'] if item.get('field') == 'footer_campaign_code'), None)
                if campaign_code_result:
                    print(f"✓ Campaign code validation: {campaign_code_result.get('status', 'UNKNOWN')}")
                    print(f"  - Expected: {campaign_code_result.get('expected', 'N/A')}")
                    print(f"  - Actual: {campaign_code_result.get('actual', 'N/A')}")
                else:
                    print("✗ Campaign code validation result not found")
                    
                # Check for campaign code match
                campaign_match_result = next((item for item in data['metadata'] if item.get('field') == 'Campaign Code - Country'), None)
                if campaign_match_result:
                    print(f"✓ Campaign code match validation: {campaign_match_result.get('status', 'UNKNOWN')}")
                    print(f"  - Expected: {campaign_match_result.get('expected', 'N/A')}")
                    print(f"  - Actual: {campaign_match_result.get('actual', 'N/A')}")
                    if 'details' in campaign_match_result:
                        print(f"  - Details: {campaign_match_result.get('details', 'N/A')}")
                else:
                    print("✗ Campaign code match validation result not found")
                    # Print all fields in metadata to debug
                    if 'metadata' in data:
                        print("Available metadata fields:")
                        for item in data['metadata']:
                            print(f"  - {item.get('field', 'unknown')}")
                        
                # Sample link data
                print("\nSample Spanish link data:")
                if data['links']:
                    first_link = data['links'][0]
                    link_info = {
                        'link_text': first_link.get('link_text', 'N/A'),
                        'url': first_link.get('url', 'N/A'),
                        'status': first_link.get('status', 'N/A'),
                        'utm_issues': first_link.get('utm_issues', [])
                    }
                    print(f"  {link_info}")
                    
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
    test_spanish_email()