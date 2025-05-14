"""
Browser automation module for Email QA System.
Uses Playwright for headless browser automation to check for product tables.
"""

import asyncio
import logging
import threading
import nest_asyncio
from urllib.parse import urlparse
from typing import Dict, Any, Optional

# Apply nest_asyncio to allow nested event loops (needed for FastAPI)
try:
    nest_asyncio.apply()
except ImportError:
    logging.warning("nest_asyncio not available - may have issues with nested event loops")
except Exception as e:
    logging.warning(f"Error applying nest_asyncio: {str(e)}")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _check_playwright_browsers_installed() -> bool:
    """Check if Playwright browsers are installed."""
    import os
    import platform
    
    try:
        system = platform.system()
        if system == "Linux":
            browser_path = os.path.expanduser("~/.cache/ms-playwright/chromium-*")
        elif system == "Darwin":  # macOS
            browser_path = os.path.expanduser("~/Library/Caches/ms-playwright/chromium-*")
        elif system == "Windows":
            browser_path = os.path.expanduser("~\\AppData\\Local\\ms-playwright\\chromium-*")
        else:
            return False
        
        # Use glob to check if the browser directory exists
        import glob
        browser_paths = glob.glob(browser_path)
        return len(browser_paths) > 0
    except Exception as e:
        logger.warning(f"Error checking Playwright browsers: {str(e)}")
        return False

async def check_for_product_tables_with_browser(url: str, timeout: Optional[int] = None) -> Dict[str, Any]:
    """
    Check if a URL's HTML contains product table classes using Playwright.
    This can bypass many bot detection systems and handle JavaScript-rendered content.
    
    Args:
        url: The URL to check for product tables
        timeout: Timeout in seconds
        
    Returns:
        dict: Detection results
    """
    try:
        # Dynamic import to handle cases where Playwright is not available
        from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
        
        # Check if browsers are installed
        if not _check_playwright_browsers_installed():
            logger.warning("Playwright browsers not installed - cannot perform browser automation")
            return {
                'found': False,
                'error': 'Playwright browsers not installed',
                'detection_method': 'browser_not_installed',
                'manual_check_required': True,
                'manual_check_message': 'Please visit this page in your browser and check for product tables with "Add to Cart" buttons'
            }
        
        # Set a reasonable timeout if not provided
        actual_timeout = (timeout or 30) * 1000  # convert to ms
        
        logger.info(f"Starting browser check for {url} with timeout {actual_timeout}ms")
        
        async with async_playwright() as p:
            # Launch browser with stealth mode
            browser = await p.chromium.launch(
                headless=True,  # True for production, False for debugging
            )
            
            # Create a "stealth" context that appears more like a real browser
            context = await browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                viewport={'width': 1280, 'height': 800},
                device_scale_factor=1,
                java_script_enabled=True,
            )
            
            # Add cookie consent handling if needed
            await context.add_init_script("""
                // Auto-accept common cookie consent prompts
                window.addEventListener('DOMContentLoaded', () => {
                    const acceptButtons = [
                        ...document.querySelectorAll('button[id*="accept"], button[id*="consent"], button[id*="cookie"]'),
                        ...document.querySelectorAll('a[id*="accept"], a[id*="consent"], a[id*="cookie"]')
                    ];
                    
                    for (const button of acceptButtons) {
                        const text = button.innerText.toLowerCase();
                        if (text.includes('accept') || text.includes('agree') || text.includes('allow')) {
                            button.click();
                            break;
                        }
                    }
                });
            """)
            
            page = await context.new_page()
            
            try:
                # Navigate with timeout
                await page.goto(url, timeout=actual_timeout, wait_until='networkidle')
                
                # Wait a bit for any lazy-loaded content
                await page.wait_for_timeout(2000)
                
                # First check for bot protection indicators
                bot_protection_result = await page.evaluate("""() => {
                    // Check for common bot protection indicators in the page
                    const botDetectionElements = [
                        // Cloudflare elements
                        document.querySelector('#cf-error-details'),
                        document.querySelector('.cf-error-code'),
                        document.querySelector('#challenge-running'),
                        document.querySelector('#challenge-spinner'),
                        document.querySelector('.cf-browser-verification'), 
                        // General captcha and security elements
                        document.querySelector('[id*="captcha"]'),
                        document.querySelector('[class*="captcha"]'),
                        document.querySelector('[id*="security"]'),
                        document.querySelector('[class*="security"]'),
                        document.querySelector('[id*="robot"]'),
                        document.querySelector('[class*="robot"]')
                    ];
                    
                    // Check if any bot protection elements are present
                    const hasBotProtection = botDetectionElements.some(el => el !== null);
                    
                    // Check for common bot protection phrases in the page text
                    const pageText = document.body.innerText.toLowerCase();
                    const botPhrases = [
                        'captcha', 'security check', 'access denied', 'blocked', 
                        'suspicious activity', 'unusual traffic', 'automated request',
                        'too many requests', 'rate limit', 'please verify', 'cloudflare',
                        'browser check', 'check your browser', 'robot', 'bot'
                    ];
                    
                    const hasBlockingText = botPhrases.some(phrase => pageText.includes(phrase));
                    
                    return {
                        bot_blocked: hasBotProtection || hasBlockingText,
                        protection_elements: hasBotProtection,
                        protection_text: hasBlockingText
                    };
                }""");
                
                # If bot protection is detected, return immediately
                if bot_protection_result.get('bot_blocked', False):
                    await browser.close()
                    logger.warning(f"Bot protection detected on {url} through browser automation")
                    return {
                        'found': False,
                        'error': 'Bot protection detected',
                        'detection_method': 'browser_automation',
                        'bot_blocked': True,
                        'protection_elements': bot_protection_result.get('protection_elements', False),
                        'protection_text': bot_protection_result.get('protection_text', False)
                    }
                
                # Check for product tables using JavaScript in the browser context
                has_product_table = await page.evaluate("""() => {
                    // IMPORTANT: Only look for the specific class names as requested
                    
                    // 1. Check for product-table* class pattern
                    const productTableElements = Array.from(document.querySelectorAll('div[class]')).filter(div => {
                        if (!div.className) return false;
                        const classNames = div.className.split(/\\s+/);
                        return classNames.some(cls => cls.startsWith('product-table'));
                    });
                    
                    if (productTableElements.length > 0) {
                        // Find the actual matching class name
                        const matchingClass = productTableElements[0].className.split(/\\s+/).find(cls => 
                            cls.startsWith('product-table')
                        );
                        
                        return {
                            found: true,
                            class_name: matchingClass || 'product-table',
                            class_pattern: 'product-table*',
                            elements_count: productTableElements.length
                        };
                    }
                    
                    // 2. Check for *productListContainer class pattern
                    const productListElements = Array.from(document.querySelectorAll('div[class]')).filter(div => {
                        if (!div.className) return false;
                        const classNames = div.className.split(/\\s+/);
                        return classNames.some(cls => cls.endsWith('productListContainer'));
                    });
                    
                    if (productListElements.length > 0) {
                        // Find the actual matching class name
                        const matchingClass = productListElements[0].className.split(/\\s+/).find(cls => 
                            cls.endsWith('productListContainer')
                        );
                        
                        return {
                            found: true,
                            class_name: matchingClass || 'productListContainer',
                            class_pattern: '*productListContainer',
                            elements_count: productListElements.length
                        };
                    }
                    
                    // No matching class found
                    return {
                        found: false,
                        message: 'No product-table* or *productListContainer class found'
                    };
                }""")
                
                await browser.close()
                
                # Format the result
                if has_product_table.get('found', False):
                    return {
                        'found': True,
                        'class_name': has_product_table.get('class_name') or has_product_table.get('id_name', 'unknown'),
                        'is_id': has_product_table.get('is_id', False),
                        'elements_count': has_product_table.get('elements_count', 1),
                        'detection_method': 'browser_automation'
                    }
                else:
                    return {
                        'found': False,
                        'has_product_content': has_product_table.get('has_product_content', False),
                        'detection_method': 'browser_automation'
                    }
                    
            except PlaywrightTimeoutError:
                await browser.close()
                logger.warning(f"Navigation timeout for {url} - possible bot protection")
                return {
                    'found': False,
                    'error': 'Navigation timeout',
                    'detection_method': 'browser_automation_timeout',
                    'bot_blocked': 'cloudflare' in url.lower() or '.cf.' in url.lower() # Assume Cloudflare timeouts are likely bot protection
                }
            except Exception as e:
                await browser.close()
                error_message = str(e).lower()
                
                # Check for bot protection indicators in error message
                bot_protection_indicators = [
                    'captcha', 'security', 'cloudflare', 'challenge', 'blocked', 
                    'denied', 'bot', 'protection', 'automated', 'detection'
                ]
                
                bot_detected = any(indicator in error_message for indicator in bot_protection_indicators)
                
                if bot_detected:
                    logger.warning(f"Likely bot protection detected in error for {url}: {error_message}")
                
                return {
                    'found': False,
                    'error': str(e),
                    'detection_method': 'browser_automation_error',
                    'bot_blocked': bot_detected
                }
    
    except ImportError:
        # Fallback if Playwright is not installed
        logger.warning("Playwright not installed. Falling back to HTTP-based checks.")
        return {
            'found': False,
            'error': 'Playwright not installed',
            'detection_method': 'fallback_http'
        }
    except Exception as e:
        logger.error(f"Browser automation error: {str(e)}")
        return {
            'found': False,
            'error': f'Browser automation error: {str(e)}',
            'detection_method': 'automation_setup_error'
        }

# Install the nest_asyncio package if it's not already installed
try:
    import nest_asyncio
except ImportError:
    try:
        import subprocess
        subprocess.check_call(["pip", "install", "nest_asyncio"])
        import nest_asyncio
    except Exception as e:
        logger.error(f"Failed to install nest_asyncio: {str(e)}")

# Helper function to synchronously run the async check
def check_for_product_tables_sync(url: str, timeout: Optional[int] = None) -> Dict[str, Any]:
    """
    Synchronous wrapper for the asynchronous browser check function.
    
    Args:
        url: The URL to check for product tables
        timeout: Timeout in seconds
        
    Returns:
        dict: Detection results
    """
    try:
        # Parse domain to check if it's a test domain
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Only use simulated responses in development mode
        from runtime_config import config
        if (config.mode == 'development' and (
            'partly-products-showcase.lovable.app' in domain or 
            'localhost:5001' in domain or 
            '127.0.0.1:5001' in domain
        )):
            # Handle test domains with special simulation parameters
            # Check URL for simulation type parameters
            if 'simulate=bot_blocked' in url or 'bot_blocked=true' in url:
                logger.info(f"Using simulated BOT BLOCKED response in development mode for test domain: {url}")
                return {
                    'found': False,
                    'error': 'Simulated bot protection (development mode)',
                    'detection_method': 'simulated',
                    'is_test_domain': True,
                    'bot_blocked': True
                }
            else:
                logger.info(f"Using simulated SUCCESS response in development mode for test domain: {url}")
                return {
                    'found': True,
                    'class_name': 'product-table productListContainer',
                    'detection_method': 'simulated',
                    'is_test_domain': True,
                    'bot_blocked': False
                }
        
        # In production mode, always use the real browser detection
        if 'partly-products-showcase.lovable.app' in domain:
            logger.info(f"Using REAL browser detection in production mode for: {url}")
            
        # We can't use asyncio.run() inside FastAPI because it's already running an event loop
        # Use a thread-based approach instead
        result_container = []
        
        def run_in_thread():
            try:
                # Create a new event loop for this thread
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                # Run the async function and get the result
                result = loop.run_until_complete(check_for_product_tables_with_browser(url, timeout))
                result_container.append(result)
                loop.close()
            except Exception as thread_e:
                logger.error(f"Thread error: {str(thread_e)}")
                # Check for bot protection indicators in error message
                error_message = str(thread_e).lower()
                bot_protection_indicators = [
                    'captcha', 'security', 'cloudflare', 'challenge', 'blocked', 
                    'denied', 'bot', 'protection', 'automated', 'detection'
                ]
                
                bot_detected = any(indicator in error_message for indicator in bot_protection_indicators)
                
                result_container.append({
                    'found': False,
                    'error': f'Thread error: {str(thread_e)}',
                    'detection_method': 'thread_error',
                    'bot_blocked': bot_detected
                })
        
        # Start a new thread
        thread = threading.Thread(target=run_in_thread)
        thread.start()
        thread.join(timeout=timeout or 60)  # Wait with timeout
        
        if thread.is_alive():
            # Thread is still running after timeout
            # For timeouts, assume possible bot protection especially for Cloudflare domains
            is_likely_bot_protection = 'cloudflare' in url.lower() or '.cf.' in url.lower()
            
            logger.warning(f"Browser check thread timed out for {url}" + 
                         (", likely bot protection" if is_likely_bot_protection else ""))
            
            return {
                'found': False,
                'error': 'Browser check thread timeout' + (', likely bot protection' if is_likely_bot_protection else ''),
                'detection_method': 'thread_timeout',
                'bot_blocked': is_likely_bot_protection
            }
        
        # Return the result if available
        if result_container:
            return result_container[0]
        else:
            # If no result was added to the container
            return {
                'found': False,
                'error': 'No result from browser check thread',
                'detection_method': 'thread_no_result',
                'bot_blocked': False
            }
            
    except Exception as e:
        logger.error(f"Error in synchronous wrapper: {str(e)}")
        # Check for bot protection indicators in error
        error_message = str(e).lower()
        bot_protection_indicators = [
            'captcha', 'security', 'cloudflare', 'challenge', 'blocked', 
            'denied', 'bot', 'protection', 'automated', 'detection'
        ]
        
        bot_detected = any(indicator in error_message for indicator in bot_protection_indicators)
        
        if bot_detected:
            logger.warning(f"Possible bot protection detected in sync wrapper error: {error_message}")
        
        return {
            'found': False,
            'error': f'Synchronous wrapper error: {str(e)}',
            'detection_method': 'sync_wrapper_error',
            'bot_blocked': bot_detected
        }

# For testing
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        url_to_test = sys.argv[1]
        print(f"Testing URL: {url_to_test}")
        result = check_for_product_tables_sync(url_to_test)
        print(f"Result: {result}")
    else:
        print("Please provide a URL to test")