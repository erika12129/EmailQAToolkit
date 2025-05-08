"""
Selenium-based browser automation for Email QA System.
Uses headless browsers with Selenium (Chrome/Firefox) for browser automation to check for product tables.
"""
import os
import threading
import time
from urllib.parse import urlparse
import concurrent.futures
import traceback
import logging
from typing import Dict, Any, Optional
import platform

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    WebDriverException,
    NoSuchElementException
)

# Use webdriver_manager for automatic driver installation
CHROME_AVAILABLE = False
FIREFOX_AVAILABLE = False
try:
    from webdriver_manager.chrome import ChromeDriverManager
    CHROME_WDM_AVAILABLE = True
except ImportError:
    CHROME_WDM_AVAILABLE = False
    class MockChromeDriverManager:
        def __init__(self):
            pass
        def install(self):
            return None
    ChromeDriverManager = MockChromeDriverManager

try:
    from webdriver_manager.firefox import GeckoDriverManager
    FIREFOX_WDM_AVAILABLE = True
except ImportError:
    FIREFOX_WDM_AVAILABLE = False
    class MockGeckoDriverManager:
        def __init__(self):
            pass
        def install(self):
            return None
    GeckoDriverManager = MockGeckoDriverManager

# Logging setup
logger = logging.getLogger(__name__)

# Global variable to track browser availability
_browser_check_complete = False
_browser_check_lock = threading.Lock()

def _check_browser_availability():
    """Check which browsers are available and set global availability flags."""
    global CHROME_AVAILABLE, FIREFOX_AVAILABLE, _browser_check_complete
    
    # Use a lock to prevent multiple threads from checking simultaneously
    with _browser_check_lock:
        # Return if already checked
        if _browser_check_complete:
            logger.info(f"Using cached browser availability: Chrome: {CHROME_AVAILABLE}, Firefox: {FIREFOX_AVAILABLE}")
            return CHROME_AVAILABLE or FIREFOX_AVAILABLE
            
        logger.info("Starting browser availability check...")
        
        # Check for Chrome
        try:
            logger.info("Checking Chrome WebDriver availability...")
            options = ChromeOptions()
            options.add_argument("--headless=new")
            options.add_argument("--disable-gpu")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            # First try with webdriver_manager
            if CHROME_WDM_AVAILABLE:
                try:
                    driver_path = ChromeDriverManager().install()
                    if driver_path and isinstance(driver_path, str):
                        service = ChromeService(executable_path=driver_path)
                        driver = webdriver.Chrome(service=service, options=options)
                        driver.quit()
                        CHROME_AVAILABLE = True
                        logger.info("Chrome WebDriver available via webdriver_manager")
                    else:
                        # Try system Chrome
                        driver = webdriver.Chrome(options=options)
                        driver.quit()
                        CHROME_AVAILABLE = True
                        logger.info("System Chrome WebDriver available")
                except Exception as e:
                    logger.info(f"Chrome WebDriver via webdriver_manager failed: {e}")
                    try:
                        # Try system Chrome
                        driver = webdriver.Chrome(options=options)
                        driver.quit()
                        CHROME_AVAILABLE = True
                        logger.info("System Chrome WebDriver available")
                    except Exception as e2:
                        logger.info(f"System Chrome WebDriver not available: {e2}")
            else:
                try:
                    # Try system Chrome directly
                    driver = webdriver.Chrome(options=options)
                    driver.quit()
                    CHROME_AVAILABLE = True
                    logger.info("System Chrome WebDriver available")
                except Exception as e:
                    logger.info(f"System Chrome WebDriver not available: {e}")
        except Exception as e:
            logger.warning(f"Error checking Chrome availability: {e}")
            
        # Check for Firefox
        try:
            logger.info("Checking Firefox WebDriver availability...")
            options = FirefoxOptions()
            options.add_argument("--headless")
            
            # First try with webdriver_manager
            if FIREFOX_WDM_AVAILABLE:
                try:
                    driver_path = GeckoDriverManager().install()
                    if driver_path and isinstance(driver_path, str):
                        service = FirefoxService(executable_path=driver_path)
                        driver = webdriver.Firefox(service=service, options=options)
                        driver.quit()
                        FIREFOX_AVAILABLE = True
                        logger.info("Firefox WebDriver available via webdriver_manager")
                    else:
                        # Try system Firefox
                        driver = webdriver.Firefox(options=options)
                        driver.quit()
                        FIREFOX_AVAILABLE = True
                        logger.info("System Firefox WebDriver available")
                except Exception as e:
                    logger.info(f"Firefox WebDriver via webdriver_manager failed: {e}")
                    try:
                        # Try system Firefox
                        driver = webdriver.Firefox(options=options)
                        driver.quit()
                        FIREFOX_AVAILABLE = True
                        logger.info("System Firefox WebDriver available")
                    except Exception as e2:
                        logger.info(f"System Firefox WebDriver not available: {e2}")
            else:
                try:
                    # Try system Firefox directly
                    driver = webdriver.Firefox(options=options)
                    driver.quit()
                    FIREFOX_AVAILABLE = True
                    logger.info("System Firefox WebDriver available")
                except Exception as e:
                    logger.info(f"System Firefox WebDriver not available: {e}")
        except Exception as e:
            logger.warning(f"Error checking Firefox availability: {e}")
            
        _browser_check_complete = True
        logger.info(f"Browser availability check complete: Chrome: {CHROME_AVAILABLE}, Firefox: {FIREFOX_AVAILABLE}")
        
        # At least one browser is available
        return CHROME_AVAILABLE or FIREFOX_AVAILABLE

def check_for_product_tables_with_selenium(url: str, timeout: Optional[int] = None) -> Dict[str, Any]:
    """
    Check if a URL's HTML contains product table classes using Selenium with available browsers.
    Tries Chrome first, then falls back to Firefox if Chrome is not available.
    
    Args:
        url: The URL to check for product tables
        timeout: Timeout in seconds
        
    Returns:
        dict: Detection results
    """
    if timeout is None:
        timeout = 10  # Default timeout
    
    # Check browser availability - this initializes CHROME_AVAILABLE and FIREFOX_AVAILABLE
    browser_available = _check_browser_availability()
    
    # Only attempt to use Selenium if at least one browser is available
    if not browser_available:
        return {
            "found": False,
            "error": "No compatible browsers available",
            "detection_method": "selenium_failed"
        }
    
    # Extract domain for logging
    try:
        domain = urlparse(url).netloc
    except:
        domain = "unknown"
    
    logger.info(f"Checking for product tables using Selenium on {domain}")
    
    driver = None
    browser_used = None
    
    try:
        # Try Chrome first if available
        if CHROME_AVAILABLE:
            try:
                logger.info(f"Using Chrome for {domain}")
                browser_used = "chrome"
                
                # Configure Chrome options
                options = ChromeOptions()
                options.add_argument("--headless=new")
                options.add_argument("--disable-gpu")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                
                # Add user agent to reduce detection as bot
                options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
                
                driver_kwargs = {}
                if CHROME_WDM_AVAILABLE:
                    try:
                        driver_path = ChromeDriverManager().install()
                        if driver_path and isinstance(driver_path, str):
                            service = ChromeService(executable_path=driver_path)
                            driver_kwargs["service"] = service
                    except Exception as e:
                        logger.debug(f"Could not use ChromeDriverManager: {e}")
                
                driver = webdriver.Chrome(options=options, **driver_kwargs)
            except Exception as e:
                logger.warning(f"Failed to initialize Chrome for {domain}: {e}")
                driver = None
        
        # Fall back to Firefox if Chrome failed or isn't available
        if driver is None and FIREFOX_AVAILABLE:
            try:
                logger.info(f"Using Firefox for {domain}")
                browser_used = "firefox"
                
                # Configure Firefox options
                options = FirefoxOptions()
                options.add_argument("--headless")
                options.add_argument("--disable-gpu")
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-dev-shm-usage")
                
                # Add user agent to reduce detection as bot
                options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Firefox/91.0")
                
                driver_kwargs = {}
                if FIREFOX_WDM_AVAILABLE:
                    try:
                        driver_path = GeckoDriverManager().install()
                        if driver_path and isinstance(driver_path, str):
                            service = FirefoxService(executable_path=driver_path)
                            driver_kwargs["service"] = service
                    except Exception as e:
                        logger.debug(f"Could not use GeckoDriverManager: {e}")
                
                driver = webdriver.Firefox(options=options, **driver_kwargs)
            except Exception as e:
                logger.warning(f"Failed to initialize Firefox for {domain}: {e}")
                return {
                    "found": False,
                    "error": f"Browser initialization failed: {str(e)[:100]}",
                    "detection_method": "selenium_browser_init_failed"
                }
        
        # If we still couldn't initialize a driver
        if driver is None:
            return {
                "found": False,
                "error": "Failed to initialize any supported browser",
                "detection_method": "selenium_no_browser"
            }
        
        # Set page load timeout
        driver.set_page_load_timeout(timeout)
        
        # Navigate to the URL
        driver.get(url)
        
        # Wait up to the timeout for the page to load completely
        time.sleep(min(2, timeout / 3))  # Give the page some time to render
        
        # Check for product table classes
        product_table_classes = [
            "product-table", 
            "productTable", 
            "product_table", 
            "productListContainer",
            "product-list-container", 
            "product-grid",
            "productGrid"
        ]
        
        found_class = None
        
        # Try to find elements with product table classes
        for class_name in product_table_classes:
            try:
                elements = driver.find_elements(By.CLASS_NAME, class_name)
                if elements:
                    found_class = class_name
                    break
            except Exception as e:
                logger.debug(f"Error searching for class {class_name}: {e}")
                continue
        
        # If we found a product table class
        if found_class:
            return {
                "found": True,
                "class_name": found_class,
                "detection_method": f"selenium_{browser_used}"
            }
        
        # Also check for elements with 'product' and 'table' in their class name
        try:
            # Use JavaScript to find elements with both 'product' and 'table' in their class
            script = """
            return Array.from(document.querySelectorAll('*')).filter(el => {
                const classes = el.className.split(/\\s+/);
                return classes.some(cls => cls.toLowerCase().includes('product')) && 
                       classes.some(cls => cls.toLowerCase().includes('table') || cls.toLowerCase().includes('list') || cls.toLowerCase().includes('grid'));
            }).map(el => el.className);
            """
            class_names = driver.execute_script(script)
            
            if class_names and len(class_names) > 0:
                return {
                    "found": True,
                    "class_name": class_names[0],
                    "detection_method": f"selenium_{browser_used}_js"
                }
        except Exception as e:
            logger.debug(f"Error executing JavaScript search: {e}")
        
        # No product table found
        return {
            "found": False,
            "detection_method": f"selenium_{browser_used}"
        }
    
    except TimeoutException:
        logger.warning(f"Timeout loading page {url}")
        return {
            "found": False,
            "error": "Timeout loading page",
            "detection_method": f"selenium_{browser_used}_timeout"
        }
    except WebDriverException as e:
        error_message = str(e)
        
        # Check for bot detection
        if "bot" in error_message.lower() or "automation" in error_message.lower():
            logger.warning(f"Possible bot detection on {url}: {e}")
            return {
                "found": False,
                "error": "Possible bot detection",
                "bot_blocked": True,
                "detection_method": f"selenium_{browser_used}_blocked"
            }
        else:
            logger.error(f"WebDriver error on {url}: {e}")
            return {
                "found": False,
                "error": f"WebDriver error: {str(e)[:100]}",
                "detection_method": f"selenium_{browser_used}_error"
            }
    except Exception as e:
        logger.error(f"Error checking {url}: {e}")
        logger.debug(traceback.format_exc())
        return {
            "found": False,
            "error": f"Error: {str(e)[:100]}",
            "detection_method": f"selenium_exception"
        }
    finally:
        # Clean up driver
        if driver:
            try:
                driver.quit()
            except:
                pass

def check_for_product_tables_selenium_sync(url: str, timeout: Optional[int] = None) -> Dict[str, Any]:
    """
    Synchronous wrapper for the selenium check function.
    
    Args:
        url: The URL to check for product tables
        timeout: Timeout in seconds
        
    Returns:
        dict: Detection results
    """
    result = {}
    
    # Use ThreadPoolExecutor to run in a separate thread with a timeout
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(check_for_product_tables_with_selenium, url, timeout)
        try:
            result = future.result(timeout=timeout if timeout else 30)
        except concurrent.futures.TimeoutError:
            logger.warning(f"Thread timeout checking {url}")
            result = {
                "found": False,
                "error": "Thread timeout",
                "detection_method": "selenium_thread_timeout"
            }
        except Exception as e:
            logger.error(f"Error in thread checking {url}: {e}")
            result = {
                "found": False,
                "error": f"Thread error: {str(e)[:100]}",
                "detection_method": "selenium_thread_error"
            }
    
    return result