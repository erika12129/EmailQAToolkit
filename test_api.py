import requests
import json
from pathlib import Path

def test_api_response():
    """
    Test the API response from the Email QA system.
    This checks if:
    1. The response has the correct content-type header
    2. The response can be parsed as valid JSON
    """
    print("Testing Email QA API...")
    
    # Set up the test files
    email_file = Path("attached_assets/Replit_test_email.html")
    requirements_file = Path("attached_assets/sample_requirements.json")
    
    if not email_file.exists():
        print(f"Error: Test email file not found at {email_file}")
        return
    
    if not requirements_file.exists():
        print(f"Error: Requirements file not found at {requirements_file}")
        return
    
    # Prepare the files for the request
    files = {
        'email': open(email_file, 'rb'),
        'requirements': open(requirements_file, 'rb')
    }
    
    # Set the headers to accept JSON
    headers = {
        'Accept': 'application/json'
    }
    
    try:
        # Make the request
        response = requests.post(
            'http://localhost:5000/run-qa',
            files=files,
            headers=headers
        )
        
        # Print response details for debugging
        print(f"Status code: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        print(f"Content-Type: {response.headers.get('content-type', 'Not specified')}")
        
        # Check if the response has the correct content type
        content_type = response.headers.get('content-type', '')
        if 'application/json' not in content_type:
            print(f"WARNING: Expected content-type to contain 'application/json', got '{content_type}'")
        else:
            print("Content-Type header is correct: application/json")
        
        # Try to parse the response as JSON
        try:
            data = response.json()
            print("Successfully parsed response as JSON")
            
            # Check if the expected keys are present
            expected_keys = ['metadata', 'links']
            for key in expected_keys:
                if key in data:
                    print(f"✓ Found expected key: '{key}'")
                else:
                    print(f"✗ Missing expected key: '{key}'")
            
            # Print a sample of the response
            print("\nSample of response data:")
            if 'metadata' in data and data['metadata']:
                print(f"First metadata item: {data['metadata'][0]}")
            
            if 'links' in data and data['links']:
                print(f"First link item: {json.dumps(data['links'][0], indent=2)}")
                
        except json.JSONDecodeError as e:
            print(f"Failed to parse response as JSON: {e}")
            print("Response text preview:", response.text[:200])
            
    except requests.RequestException as e:
        print(f"Request failed: {e}")
    
    finally:
        # Close the files
        for f in files.values():
            f.close()

if __name__ == "__main__":
    test_api_response()