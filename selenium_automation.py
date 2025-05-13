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

# Add a public function to check if any browsers are available
def check_browser_availability():
    """
    Check if any browsers are actually available and installed.
    This is different from importing the Selenium library - it checks if
    Chrome or Firefox are actually installed on the system.
    
    Returns:
        bool: True if at least one browser is available, False otherwise
    """
    global CHROME_AVAILABLE, FIREFOX_AVAILABLE
    
    if not _browser_check_complete:
        # Try to detect browsers
        _check_browser_availability()
    
    # Return True if any browser is available
    return CHROME_AVAILABLE or FIREFOX_AVAILABLE

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
            options.add_argument("--disable-setuid-sandbox")
            
            # Set binary location for Chrome in deployment
            if os.environ.get('DEPLOYMENT_ENVIRONMENT') == 'True':
                options.binary_location = "/usr/bin/google-chrome-stable"
            
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
        
        try:
            # Navigate to the URL
            driver.get(url)
            
            # Check for 404 errors in common ways
            if "404" in driver.title or "not found" in driver.title.lower():
                driver.quit()
                return {
                    "found": False,
                    "error": "Page not found (HTTP 404)",
                    "detection_method": "selenium",
                    "bot_blocked": False,  # Important: 404 is not bot protection
                    "http_status": 404
                }
        except Exception as e:
            # Check for specific error messages that indicate a 404
            error_msg = str(e).lower()
            if "404" in error_msg or "not found" in error_msg:
                driver.quit()
                return {
                    "found": False,
                    "error": "Page not found (HTTP 404)",
                    "detection_method": "selenium",
                    "bot_blocked": False,  # Important: 404 is not bot protection
                    "http_status": 404
                }
            # For other errors, we'll just continue and let the regular error handling deal with it
            logger.warning(f"Navigation error (attempting to continue): {e}")
        
        # Wait up to the timeout for the page to load completely
        time.sleep(min(2, timeout / 3))  # Give the page some time to render
        
        # IMPORTANT: Only check for these specific class patterns
        # 1. "product-table*" (starts with "product-table")
        # 2. "*productListContainer" (ends with "productListContainer")
        # We'll use JavaScript to find elements with these class patterns
        
        # We'll use JavaScript to find elements with the specific class patterns we need
        try:
            # Script to find divs with class names matching our specific patterns
            script = """
            // Function to check if a div has the specific class patterns we're looking for
            function checkForProductTables() {
                // Results container
                const results = {
                    found: false,
                    class_name: null,
                    pattern: null
                };
                
                // 1. Look for product-table* pattern (starts with product-table)
                // Get all elements with any class attribute
                const allElementsWithClass = Array.from(document.querySelectorAll('*[class]'));
                
                // Filter for product-table pattern
                const productTableElements = allElementsWithClass.filter(element => {
                    if (!element.className || typeof element.className !== 'string') return false;
                    const classNames = element.className.split(/\\s+/);
                    return classNames.some(cls => 
                        cls.startsWith('product-table') || 
                        cls.includes('product-table') ||
                        cls.includes('product_table')
                    );
                });
                
                if (productTableElements.length > 0) {
                    // Find the actual matching class name
                    const matchingDiv = productTableElements[0];
                    const matchingClass = matchingDiv.className.split(/\\s+/).find(cls => 
                        cls.startsWith('product-table')
                    );
                    
                    results.found = true;
                    results.class_name = matchingClass || 'product-table';
                    results.pattern = 'product-table*';
                    results.elements_count = productTableElements.length;
                    return results;
                }
                
                // 2. Look for product-related patterns across various web technologies
                // - More comprehensive search to handle any web technology, not just React
                const productListElements = allElementsWithClass.filter(element => {
                    // Skip elements without className or non-string classNames
                    if (!element.className || typeof element.className !== 'string') return false;
                    
                    const classNames = element.className.split(/\\s+/);
                    
                    // Check for product-related classes - very broad patterns to catch most implementations
                    return classNames.some(cls => 
                        cls.endsWith('productListContainer') || 
                        cls.includes('product') ||
                        cls.includes('item-list') ||
                        cls.includes('catalog') ||
                        cls.includes('shop-items') ||
                        cls.includes('store-products') ||
                        cls.includes('merchandise') ||
                        cls.includes('goods-display') ||
                        cls.includes('listing-grid') ||
                        cls.includes('carousel-products') ||
                        cls.includes('selling-items') ||
                        cls.includes('ecommerce') ||
                        cls.includes('shop')
                    );
                });
                
                // Also check for product-related elements by ID
                if (productListElements.length === 0) {
                    const elementsWithId = Array.from(document.querySelectorAll('*[id]'));
                    const productElementsById = elementsWithId.filter(el => {
                        if (!el.id) return false;
                        return (
                            el.id.includes('product') ||
                            el.id.includes('catalog') ||
                            el.id.includes('shop')
                        );
                    });
                    
                    if (productElementsById.length > 0) {
                        return {
                            found: true,
                            class_name: `id:${productElementsById[0].id}`,
                            class_pattern: 'product-id-detection',
                            elements_count: productElementsById.length
                        };
                    }
                }
                
                if (productListElements.length > 0) {
                    // Find the actual matching class name with more flexibility
                    const matchingDiv = productListElements[0];
                    const classStr = matchingDiv.className;
                    let matchingClass = '';
                    
                    // Check for various product-related classes
                    const classArr = classStr.split(/\\s+/);
                    for (const cls of classArr) {
                        if (cls.includes('product')) {
                            matchingClass = cls;
                            break;
                        }
                    }
                    
                    results.found = true;
                    results.class_name = matchingClass || 'productListContainer';
                    results.pattern = '*productListContainer';
                    results.elements_count = productListElements.length;
                    return results;
                }
                
                // Nothing found
                return results;
            }
            
            // Run the check and return results
            return checkForProductTables();
            """
            
            # Execute the script
            result = driver.execute_script(script)
            
            if result and result.get('found', False):
                logger.info(f"Found product table via JavaScript: {result}")
                return {
                    "found": True,
                    "class_name": result.get('class_name', 'unknown'),
                    "pattern": result.get('pattern', 'unknown'),
                    "elements_count": result.get('elements_count', 1),
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