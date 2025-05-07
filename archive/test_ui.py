from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

def test_upload_form():
    """Test the email QA form submission using Selenium."""
    print("Setting up Chrome WebDriver...")
    
    # Configure Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Initialize the WebDriver
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Navigate to the Email QA page
        print("Opening the Email QA application...")
        driver.get("http://localhost:5000/")
        
        # Wait for the page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "qa-form"))
        )
        print("Page loaded successfully")
        
        # Take a screenshot for verification
        driver.save_screenshot("email_qa_page.png")
        print("Screenshot saved to email_qa_page.png")
        
        # Get the test files
        email_file = os.path.abspath("attached_assets/Replit_test_email.html")
        req_file = os.path.abspath("attached_assets/sample_requirements.json")
        
        if not os.path.exists(email_file):
            print(f"Error: Test email file not found at {email_file}")
            return
            
        if not os.path.exists(req_file):
            print(f"Error: Requirements file not found at {req_file}")
            return
        
        # Upload the email file
        print("Uploading test email file...")
        email_input = driver.find_element(By.ID, "email-file")
        email_input.send_keys(email_file)
        
        # Switch to JSON file upload
        print("Switching to JSON file upload...")
        json_toggle = driver.find_element(By.ID, "json-switch")
        json_toggle.click()
        
        # Upload the requirements file
        print("Uploading requirements file...")
        req_input = driver.find_element(By.ID, "req-file")
        req_input.send_keys(req_file)
        
        # Submit the form
        print("Submitting the form...")
        submit_button = driver.find_element(By.ID, "submit-button")
        submit_button.click()
        
        # Wait for the results to load
        try:
            WebDriverWait(driver, 20).until(
                EC.visibility_of_element_located((By.ID, "results-container"))
            )
            print("Results loaded successfully!")
            
            # Take a screenshot of the results
            driver.save_screenshot("email_qa_results.png")
            print("Results screenshot saved to email_qa_results.png")
            
            # Check if there's an error message
            error_message = driver.find_element(By.ID, "error-message")
            if error_message.is_displayed():
                print(f"Error displayed: {error_message.text}")
            else:
                print("No error message displayed")
                
            # Get some data from the results to verify
            metadata_table = driver.find_element(By.ID, "metadata-results")
            rows = metadata_table.find_elements(By.TAG_NAME, "tr")
            if rows:
                print(f"Found {len(rows)} metadata results")
                
            links_table = driver.find_element(By.ID, "links-results")
            link_rows = links_table.find_elements(By.TAG_NAME, "tr")
            if link_rows:
                print(f"Found {len(link_rows)} link results")
                
            print("Test completed successfully!")
            
        except Exception as e:
            print(f"Error waiting for results: {e}")
            # Take a screenshot to see what happened
            driver.save_screenshot("error_state.png")
            print("Error state screenshot saved to error_state.png")
            
            # Check if there's an error message shown
            try:
                error_element = driver.find_element(By.ID, "error-message")
                if error_element.is_displayed():
                    print(f"Error message displayed: {error_element.text}")
            except:
                print("No error element found")
    
    except Exception as e:
        print(f"Test failed: {e}")
        
    finally:
        # Close the browser
        driver.quit()

if __name__ == "__main__":
    test_upload_form()