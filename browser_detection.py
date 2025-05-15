"""
Browser detection module for Email QA System.
This module detects and configures available browsers in the environment.
"""

import logging
import os
import subprocess
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_chrome_installed():
    """Check if Chrome/Chromium is installed in the system."""
    try:
        # Try to run chrome with version flag
        process = subprocess.run(
            ["chromium", "--version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        if process.returncode == 0:
            version = process.stdout.strip()
            logger.info(f"Chrome detected: {version}")
            return True, version
        else:
            # Try alternative command names
            process = subprocess.run(
                ["google-chrome", "--version"], 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            if process.returncode == 0:
                version = process.stdout.strip()
                logger.info(f"Chrome detected: {version}")
                return True, version
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        logger.warning(f"Chrome detection error: {e}")
    
    logger.warning("Chrome not found in system")
    return False, None

def check_firefox_installed():
    """Check if Firefox is installed in the system."""
    try:
        # Try to run firefox with version flag
        process = subprocess.run(
            ["firefox", "--version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        if process.returncode == 0:
            version = process.stdout.strip()
            logger.info(f"Firefox detected: {version}")
            return True, version
        
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        logger.warning(f"Firefox detection error: {e}")
    
    logger.warning("Firefox not found in system")
    return False, None

def check_browser_drivers():
    """Check if WebDriver executables are available."""
    chrome_driver = False
    firefox_driver = False
    
    # Check ChromeDriver
    try:
        process = subprocess.run(
            ["chromedriver", "--version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        if process.returncode == 0:
            version = process.stdout.strip()
            logger.info(f"ChromeDriver detected: {version}")
            chrome_driver = True
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        logger.warning(f"ChromeDriver detection error: {e}")
    
    # Check GeckoDriver
    try:
        process = subprocess.run(
            ["geckodriver", "--version"], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True,
            timeout=5
        )
        if process.returncode == 0:
            version = process.stdout.strip()
            logger.info(f"GeckoDriver detected: {version}")
            firefox_driver = True
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        logger.warning(f"GeckoDriver detection error: {e}")
    
    return chrome_driver, firefox_driver

def configure_browser_paths():
    """Configure browser binary paths for automated detection in Selenium."""
    # Set environment variables for WebDriver to find browsers
    # This is critical for deployment environments where browsers may be in non-standard locations
    
    # Try to locate Chrome/Chromium binary
    chrome_paths = [
        "/usr/bin/chromium",
        "/usr/bin/chromium-browser",
        "/usr/bin/google-chrome",
        "/nix/store/chromium",
        # Add additional paths as needed
    ]
    
    chrome_found = False
    for path in chrome_paths:
        if os.path.exists(path):
            os.environ["CHROME_BINARY_PATH"] = path
            logger.info(f"Set Chrome binary path to {path}")
            chrome_found = True
            break
    
    if not chrome_found:
        logger.warning("Could not locate Chrome binary. Browser automation may not work correctly.")
    
    # Try to locate Firefox binary
    firefox_paths = [
        "/usr/bin/firefox",
        "/nix/store/firefox",
        # Add additional paths as needed
    ]
    
    firefox_found = False
    for path in firefox_paths:
        if os.path.exists(path):
            os.environ["FIREFOX_BINARY_PATH"] = path
            logger.info(f"Set Firefox binary path to {path}")
            firefox_found = True
            break
    
    if not firefox_found:
        logger.warning("Could not locate Firefox binary. Browser automation may not work correctly.")
    
    return chrome_found, firefox_found

def check_cloud_browser_available():
    """Check if cloud browser automation is available via API keys."""
    # Check for ScrapingBee API key
    scrapingbee_key = os.environ.get('SCRAPINGBEE_API_KEY', '')
    if scrapingbee_key:
        logger.info(f"ScrapingBee API key found - cloud browser automation available: {scrapingbee_key[:4]}...")
        return True
    
    # Check for Browserless API key
    browserless_key = os.environ.get('BROWSERLESS_API_KEY', '')
    if browserless_key:
        logger.info(f"Browserless API key found - cloud browser automation available: {browserless_key[:4]}...")
        return True
    
    # Log environment variables for debugging
    env_vars = {k: v[:4]+'...' if k in ['SCRAPINGBEE_API_KEY', 'BROWSERLESS_API_KEY'] and v else v 
               for k, v in os.environ.items() 
               if k in ['SCRAPINGBEE_API_KEY', 'BROWSERLESS_API_KEY']}
    
    logger.info(f"No cloud browser API keys found in environment: {env_vars}")
    return False

def run_full_detection():
    """Run all detection steps and configure environment for browser automation."""
    logger.info("Starting browser detection and configuration...")
    
    # First check for Replit environment since cloud browser is our primary option there
    repl_id = os.environ.get('REPL_ID')
    replit_env = os.environ.get('REPLIT_ENVIRONMENT')
    is_replit = repl_id is not None or replit_env is not None
    is_deployed = replit_env == 'production'
    
    # Check if cloud browser automation is available
    cloud_browser_available = check_cloud_browser_available()
    
    # In Replit environment, we focus on cloud browser availability
    if is_replit:
        if is_deployed:
            logger.info("Replit deployment environment detected - prioritizing cloud browser automation")
        else:
            logger.info("Replit development environment detected - skipping local browser checks")
            
        # In both development and deployment Replit, if cloud browser is available, use it
        if cloud_browser_available:
            logger.info("Cloud browser automation is available in Replit - browser checks complete")
            return True
            
        # Log if cloud browser is not available
        logger.info("No cloud browser automation available in Replit - local browser automation will not work")
        
        # If we're running in a Replit environment and checking for Chrome/Firefox,
        # just skip this check to avoid unnecessary delays
        logger.info("Skipping browser availability check in Replit environment")
        return cloud_browser_available
    
    # If cloud browser is available in any environment, we can use it
    if cloud_browser_available:
        logger.info("Cloud browser automation is available - skipping local browser checks")
        return True
    
    # If no cloud browser, check for local browsers
    chrome_installed, chrome_version = check_chrome_installed()
    firefox_installed, firefox_version = check_firefox_installed()
    
    chrome_driver, firefox_driver = check_browser_drivers()
    
    chrome_path, firefox_path = configure_browser_paths()
    
    # Report findings
    if chrome_installed and chrome_driver and chrome_path:
        logger.info("Chrome automation setup complete and ready")
    else:
        logger.warning("Chrome automation setup incomplete: " +
                      f"browser={'✓' if chrome_installed else '✗'}, " +
                      f"driver={'✓' if chrome_driver else '✗'}, " +
                      f"path={'✓' if chrome_path else '✗'}")
    
    if firefox_installed and firefox_driver and firefox_path:
        logger.info("Firefox automation setup complete and ready")
    else:
        logger.warning("Firefox automation setup incomplete: " +
                      f"browser={'✓' if firefox_installed else '✗'}, " +
                      f"driver={'✓' if firefox_driver else '✗'}, " +
                      f"path={'✓' if firefox_path else '✗'}")
    
    # Return overall status - cloud browser OR local browser
    local_browser_available = (chrome_installed and chrome_driver and chrome_path) or \
                              (firefox_installed and firefox_driver and firefox_path)
    
    overall_available = cloud_browser_available or local_browser_available
    logger.info(f"Overall browser automation available: {overall_available} (Cloud: {cloud_browser_available}, Local: {local_browser_available})")
    
    return overall_available

if __name__ == "__main__":
    # If run directly, perform detection and print status
    status = run_full_detection()
    print(f"Browser automation available: {'Yes' if status else 'No'}")
    sys.exit(0 if status else 1)