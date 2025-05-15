"""
Simple mode-switching implementation for the Email QA System.
Enhanced with hybrid browser automation for better product table detection.
Now with cloud browser automation support.
"""

import os
import shutil
import tempfile
import logging
import json
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Body, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional, List, Dict, Any
import email_qa_enhanced
from email_qa_enhanced import validate_email
from runtime_config import config

# Import cloud browser API endpoints module
try:
    from api_endpoints import router as api_router
    CLOUD_API_ENDPOINTS_AVAILABLE = True
    logging.info("Cloud API endpoints module loaded successfully")
except ImportError:
    CLOUD_API_ENDPOINTS_AVAILABLE = False
    api_router = None  # Set it to None to avoid "possibly unbound" error
    logging.warning("Cloud API endpoints module not available")

# Import cloud browser API test module if available
try:
    import cloud_api_test
    CLOUD_API_TEST_AVAILABLE = True
    logging.info("Cloud API test module loaded successfully")
except ImportError:
    CLOUD_API_TEST_AVAILABLE = False
    logging.warning("Cloud API test module not available")

# Import browser automation module
# Define a fallback function in case the real one isn't available
def browser_check_fallback(url, timeout=None):
    """
    Fallback function when browser automation is not available.
    Preserves the bot_blocked flag when falling back from HTTP checks.
    """
    # If we're in development mode and this is a test domain, we can simulate responses
    from urllib.parse import urlparse
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    
    if config.mode == 'development' and (
        'partly-products-showcase.lovable.app' in domain or 
        'localhost:5001' in domain or 
        '127.0.0.1:5001' in domain
    ):
        # Simulate bot blocked if requested in URL params
        if 'simulate=bot_blocked' in url or 'bot_blocked=true' in url:
            logging.info(f"Simulating bot blocked in fallback for: {url}")
            return {
                'found': False,
                'error': "Simulated bot protection (development mode)",
                'detection_method': 'simulated',
                'bot_blocked': True
            }
        else:
            # Simulate success for test domains in development mode
            logging.info(f"Simulating product table found in fallback for: {url}")
            return {
                'found': True,
                'class_name': 'product-table',
                'detection_method': 'simulated',
                'bot_blocked': False
            }
    
    # For all other cases, return standard fallback
    return {
        'found': False,
        'error': "Browser automation not available",
        'detection_method': 'unavailable',
        'bot_blocked': False
    }

# Check for text analysis availability
TEXT_ANALYSIS_AVAILABLE = False
try:
    from web_scraper import check_for_product_tables_with_text_analysis
    TEXT_ANALYSIS_AVAILABLE = True
    logging.info("Text analysis module loaded successfully - enhanced detection available in mode switcher")
except ImportError:
    logging.warning("Text analysis module not available in mode switcher - some advanced detection features will be disabled")
    
    # Define a fallback function to prevent unbound errors
    def check_for_product_tables_with_text_analysis(url):
        logging.warning(f"Text analysis called but not available for {url}")
        return {
            'found': False,
            'error': "Text analysis module not available",
            'detection_method': 'text_analysis_unavailable',
            'confidence_score': 0
        }

# Try to import the Selenium browser check function
try:
    from selenium_automation import check_for_product_tables_selenium_sync as browser_check
    BROWSER_AUTOMATION_AVAILABLE = True
    logging.info("Selenium browser automation module loaded successfully")
except ImportError:
    browser_check = browser_check_fallback  # Use the fallback function
    BROWSER_AUTOMATION_AVAILABLE = False
    logging.warning("Browser automation module not available. Using HTTP-only checks.")

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Email QA Automation API")

# Configure CORS with more aggressive settings for deployment environments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_origin_regex=".*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Include cloud browser API endpoints router if available
if CLOUD_API_ENDPOINTS_AVAILABLE and api_router is not None:
    try:
        app.include_router(api_router, prefix="/api/cloud")
        logging.info("Cloud browser API endpoints added to FastAPI application")
    except Exception as e:
        logging.error(f"Failed to include cloud browser API endpoints: {e}")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount attached assets
app.mount("/attached_assets", StaticFiles(directory="attached_assets"), name="attached_assets")

@app.get("/")
async def read_root():
    """Serve the frontend application with mode indicator."""
    with open("static/index.html", "r") as f:
        html_content = f.read()
        
    # Add mode indicator to the UI
    mode = config.mode
    color = "#e53e3e" if mode == "production" else "#3182ce"
    
    mode_indicator = f"""
    <div style="position: fixed; bottom: 10px; right: 10px; 
         background-color: {color}; 
         color: white; padding: 6px 12px; border-radius: 4px; 
         font-size: 12px; font-weight: bold; z-index: 1000;">
        <span>Mode: {mode.upper()}</span>
        <a href="/set-mode/{'development' if mode == 'production' else 'production'}" 
           style="margin-left: 8px; color: white; font-weight: bold; text-decoration: underline;">
           Switch
        </a>
    </div>
    """
    
    # Add data-mode attribute to the body tag for JavaScript detection
    html_content = html_content.replace("<body", f"<body data-mode=\"{mode}\"")
    
    # Insert the mode indicator before the closing body tag
    html_content = html_content.replace("</body>", f"{mode_indicator}</body>")
    
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/test")
async def test_page():
    """Serve a simple test page directly."""
    with open("static/simple.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/config")
async def get_config():
    """Get current configuration settings."""
    # For Replit deployment, SKIP the browser availability check and use cloud browser only
    cloud_browser_available = False
    
    # Fast check if we're in Replit
    is_replit = os.environ.get('REPL_ID') is not None or os.environ.get('REPLIT_ENVIRONMENT') is not None
    
    if is_replit:
        # In Replit, we only check for API keys, not for browser installation
        scrapingbee_key = os.environ.get('SCRAPINGBEE_API_KEY', '')
        browserless_key = os.environ.get('BROWSERLESS_API_KEY', '')
        cloud_browser_available = bool(scrapingbee_key or browserless_key)
        logger.info(f"Replit environment detected, using cloud browser availability: {cloud_browser_available}")
    else:
        # Only in non-Replit environments, check traditionally
        try:
            from browser_detection import check_cloud_browser_available
            cloud_browser_available = check_cloud_browser_available()
        except Exception as e:
            logger.error(f"Error checking cloud browser availability: {str(e)}")
            cloud_browser_available = False
    
    # In Replit, we use cloud browser availability as the overall availability
    browser_automation_available = cloud_browser_available if is_replit else (BROWSER_AUTOMATION_AVAILABLE or cloud_browser_available)
    
    # Check if this is a deployment environment (Replit production)
    is_deployment = os.environ.get("REPL_SLUG") is not None and os.environ.get("REPL_OWNER") is not None
    
    return JSONResponse(content={
        "mode": config.mode,
        "enable_test_redirects": config.enable_test_redirects,
        "product_table_timeout": config.product_table_timeout,
        "request_timeout": config.request_timeout,
        "max_retries": config.max_retries,
        "test_domains": config.test_domains,
        "browser_automation_available": browser_automation_available,
        "cloud_browser_available": cloud_browser_available,
        "is_deployment": is_deployment
    })

@app.get("/api/production-domain-status")
@app.get("/production-domain-status")
async def production_domain_status(request: Request):
    """Special diagnostic endpoint for production domains."""
    # Check if this is an HTML request (Accept header contains text/html)
    accept_header = request.headers.get('accept', '')
    if 'text/html' in accept_header:
        # Return the HTML page
        with open("static/domain-status.html", "r") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)
    # This endpoint helps debug issues in the deployed environment
    partly_showcase_url = "https://partly-products-showcase.lovable.app"
    
    # Check if we're in production mode
    is_production = config.mode == 'production'
    
    # In production, partly-products-showcase.lovable.app should NOT be considered a test domain
    if config.mode == 'production':
        is_test_domain = False
    else:
        # In development mode, treat partly-products-showcase.lovable.app as a test domain
        is_test_domain = True
    
    import datetime
    
    # Return comprehensive diagnostic info
    return JSONResponse(content={
        "mode": config.mode,
        "is_production": is_production,
        "partly_showcase_url": partly_showcase_url,
        "is_test_domain": is_test_domain,
        "test_redirects_enabled": config.enable_test_redirects,
        "expect_bot_protection": is_production and not is_test_domain,
        "should_display_as": "Check blocked (orange)" if (is_production and not is_test_domain) else "Yes (green)",
        "timestamp": datetime.datetime.now().isoformat()
    })

@app.get("/set-mode/{mode}")
async def set_mode(mode: str):
    """
    Set application mode (development/production).
    
    Args:
        mode: 'development' or 'production'
    """
    try:
        if mode not in ["development", "production"]:
            return HTMLResponse(
                content=f"<h1>Invalid mode: {mode}</h1><p>Use 'development' or 'production'</p>",
                status_code=400
            )
            
        config.set_mode(mode)
        return HTMLResponse(
            content=f"""
            <html>
                <head>
                    <meta http-equiv="refresh" content="1;url=/" />
                    <title>Mode changed</title>
                </head>
                <body>
                    <h1>Mode changed to {mode}</h1>
                    <p>Redirecting to home page...</p>
                </body>
            </html>
            """,
            status_code=200
        )
    except Exception as e:
        return HTMLResponse(
            content=f"<h1>Error</h1><p>{str(e)}</p>",
            status_code=500
        )

# Multiple formats of the same endpoint to handle various deployment scenarios
@app.post("/api/check-product-tables")
@app.post("/api/check_product_tables") 
@app.post("/check_product_tables")  # Add non-API prefixed version 
@app.post("/check-product-tables")  # Additional non-API endpoint for compatibility
@app.post("/product-tables-check")  # Extra route to catch more variations
@app.get("/api/check_simple") # Simple GET endpoint for testing connectivity
@app.get("/api/check-product-tables/simple") # Additional test endpoint for production
async def check_product_tables(
    urls: list = Body(..., description="List of URLs to check for product tables"),
    timeout: Optional[int] = Body(None, description="Timeout for product table checks in seconds")
):
    """
    Check if the specified URLs contain product tables.
    This endpoint allows for checking selected links after initial validation,
    with an adjustable timeout to prevent hanging the main validation process.
    
    Args:
        urls: List of URLs to check for product tables
        timeout: Timeout for each check in seconds (defaults to config setting)
        
    Returns:
        dict: Results of product table detection for each URL
    """
    try:
        if not urls:
            return JSONResponse(
                status_code=400,
                content={"error": "No URLs provided"}
            )
            
        results = {}
        for url in urls:
            try:
                # Log the URL we're checking
                logger.info(f"Processing product table check for URL: {url}")
                
                # Handle test domains differently depending on mode
                # In production, partly-products-showcase.lovable.app should NOT be considered a test domain
                if config.mode == 'production':
                    is_test_domain = ('localhost:5001' in url or '127.0.0.1:5001' in url)
                else:
                    # In development mode, also treat partly-products-showcase.lovable.app as a test domain
                    is_test_domain = ('partly-products-showcase.lovable.app' in url or 
                                    'localhost:5001' in url or 
                                    '127.0.0.1:5001' in url)
                
                # In development mode, use simulated results for test domains
                if (config.mode == 'development' and is_test_domain):
                    # Check if we should simulate bot protection instead
                    if 'simulate=bot_blocked' in url or 'bot_blocked=true' in url:
                        logger.info(f"Using simulated BOT BLOCKED response for test domain in development mode: {url}")
                        results[url] = {
                            'found': False,
                            'error': 'Simulated bot protection (development mode)',
                            'detection_method': 'simulated',
                            'is_test_domain': True,
                            'bot_blocked': True
                        }
                    else:
                        # Standard simulated success
                        logger.info(f"Using simulated success response for test domain in development mode: {url}")
                        # For test domains in development mode, return a simulated positive result
                        results[url] = {
                            'found': True, 
                            'class_name': 'product-table productListContainer',
                            'detection_method': 'simulated',
                            'is_test_domain': True,
                            'bot_blocked': False
                        }
                # In production mode for partly-products-showcase.lovable.app, use REAL detection
                elif ('partly-products-showcase.lovable.app' in url):
                    logger.info(f"[PRODUCTION DOMAIN] Using REAL detection for partly-products-showcase domain: {url}")
                    # Add extra debug logging for production troubleshooting
                    print(f"[PRODUCTION DOMAIN] Processing URL: {url} with REAL detection")
                    print(f"[PRODUCTION DOMAIN] Current mode: {config.mode}")
                    # Output is_test_domain value for debugging
                    is_test_domain = False
                    print(f"[PRODUCTION DOMAIN] is_test_domain set to: {is_test_domain}")
                    
                    # Check if browser automation is actually available with real browsers
                    browsers_actually_available = False
                    try:
                        # Check if browsers are actually installed (not just the automation library)
                        if BROWSER_AUTOMATION_AVAILABLE:
                            from selenium_automation import check_browser_availability
                            browsers_actually_available = check_browser_availability()
                            logger.info(f"Browser availability check result: {browsers_actually_available}")
                    except Exception as browser_check_error:
                        logger.warning(f"Could not verify browser availability: {str(browser_check_error)}")
                        browsers_actually_available = False
                    
                    # Use HTTP detection first - treating this as a REAL production domain
                    logger.info(f"Using HTTP detection method for {url} in production")
                    http_result = email_qa_enhanced.check_for_product_tables(url, timeout=timeout)
                    # Use browser_unavailable for detection_method to ensure consistent reporting
                    http_result['detection_method'] = 'browser_unavailable'
                    http_result['is_test_domain'] = False  # Explicitly mark as NOT a test domain
                    
                    # Use standardized message if browser automation is unavailable
                    if http_result.get('found') is None or http_result.get('message', '').startswith('Browser automation unavailable'):
                        http_result['message'] = 'Unknown - Browser automation unavailable - manual verification required'
                    
                    # If product tables are found, use that result
                    if http_result.get('found', False):
                        logger.info(f"HTTP method found product tables for {url} in production mode")
                        results[url] = http_result
                    else:
                        # Even if bot blocking detected, don't simulate - handle it like any other site
                        # This ensures it behaves like a real production site
                        results[url] = http_result
                        
                    # Try browser automation as a fallback if needed
                    # We already verified browser availability above
                    if not results[url].get('found', False) and BROWSER_AUTOMATION_AVAILABLE:
                        logger.info(f"HTTP method did not find product tables, trying browser automation for {url}")
                        try:
                            browser_result = browser_check(url, timeout=timeout)
                            browser_result['detection_method'] = 'browser_production'
                            browser_result['is_test_domain'] = False  # Explicitly mark as NOT a test domain
                            
                            # If browser found something, use that result
                            if browser_result.get('found', False):
                                logger.info(f"Browser automation found product tables for {url} in production")
                                results[url] = browser_result
                        except Exception as e:
                            logger.warning(f"Browser automation failed in production mode for {url}: {str(e)}")
                        
                    # Try text analysis for all URLs where browser automation isn't available
                    # This is more proactive - we use text analysis not just as a last resort
                    if TEXT_ANALYSIS_AVAILABLE:
                        try:
                            logger.info(f"Using text-based detection for {url}")
                            text_result = check_for_product_tables_with_text_analysis(url)
                            text_result['detection_method'] = 'browser_unavailable'
                            text_result['is_test_domain'] = False  # Explicitly mark as NOT a test domain
                            
                            # If text analysis gives a confident result, use it
                            if text_result.get('found', True) and text_result.get('confidence') in ['high', 'medium']:
                                logger.info(f"Text analysis found product content with {text_result.get('confidence')} confidence for {url}")
                                results[url] = text_result
                            # CRITICAL FIX: For URLs in the /products/ path, we should NEVER use URL pattern matching
                            # in Replit environment - always return Unknown result requiring manual verification
                            # Using more specific matching to ensure we only catch actual product paths
                            elif '/products/' in url or '/product/' in url or url.endswith('/products'):
                                logger.info(f"CRITICAL FIX: URL {url} contains product path - NOT using URL pattern matching")
                                # Return Unknown result that requires manual verification
                                results[url] = {
                                    'found': None,
                                    'class_name': None,
                                    'detection_method': 'browser_unavailable',
                                    'message': 'Unknown - Browser automation unavailable - manual verification required',
                                    'is_test_domain': False
                                }
                            # Otherwise, keep the current result
                        except Exception as text_error:
                            logger.warning(f"Text analysis failed for {url}: {str(text_error)}")
                else:
                    # Use hybrid approach for better detection - try browser automation first with fallback to HTTP
                    if BROWSER_AUTOMATION_AVAILABLE:
                        # Try browser automation first
                        logger.info(f"Attempting browser-based check for {url}")
                        try:
                            result = browser_check(url, timeout=timeout)
                            logger.info(f"Browser check completed for {url} with result: {result}")
                            
                            # If browser check fails but it's not a timeout (which is a real result),
                            # we should try the HTTP method as fallback
                            error_msg = result.get('error', '')
                            if (not result.get('found', False) and 
                                error_msg and 
                                not (isinstance(error_msg, str) and 'timeout' in error_msg.lower())):
                                logger.info(f"Browser check didn't find product tables for {url}, trying HTTP fallback")
                                http_result = email_qa_enhanced.check_for_product_tables(url, timeout=timeout)
                                
                                # If HTTP method finds something or gives more specific details, use that result
                                if http_result.get('found', False):
                                    logger.info(f"HTTP fallback found product tables for {url}")
                                    http_result['detection_method'] = 'http_fallback_after_selenium'
                                    result = http_result
                        except Exception as browser_error:
                            # Handle exceptions during browser automation
                            logger.warning(f"Browser automation error for {url}: {str(browser_error)}")
                            logger.info(f"Using HTTP fallback due to browser automation error")
                            result = email_qa_enhanced.check_for_product_tables(url, timeout=timeout)
                            result['detection_method'] = 'http_fallback_after_error'
                            
                            # Make sure bot_blocked flag is preserved (very important!)
                            if result.get('bot_blocked', False):
                                logger.warning(f"Bot blocking detected for {url} during fallback - will report this in the response")
                    else:
                        # Browser automation is not available, use direct HTTP check
                        logger.info(f"Browser automation not available, using direct HTTP check for {url}")
                        result = email_qa_enhanced.check_for_product_tables(url, timeout=timeout)
                        
                        # Add additional context to the result to show we used direct HTTP
                        if 'detection_method' not in result:
                            result['detection_method'] = 'direct_http'
                            
                        # Make sure bot_blocked flag is preserved (very important!)
                        if result.get('bot_blocked', False):
                            logger.warning(f"Bot blocking detected for {url} - will report this in the response")
                    
                    logger.info(f"Product table check result for {url}: {result}")
                    results[url] = result
            except Exception as url_error:
                # Handle errors for individual URLs separately
                logger.error(f"Error checking product table for URL {url}: {str(url_error)}")
                
                # For Cloudflare domains or other known bot protection, add bot_blocked flag
                if 'cloudflare' in url.lower() or 'captcha' in str(url_error).lower() or 'bot' in str(url_error).lower():
                    logger.warning(f"Likely bot protection detected from error handling for {url}")
                    results[url] = {
                        'found': False,
                        'error': f"Error processing URL: {str(url_error)}",
                        'detection_method': 'error',
                        'bot_blocked': True
                    }
                else:
                    results[url] = {
                        'found': False,
                        'error': f"Error processing URL: {str(url_error)}",
                        'detection_method': 'error'
                    }
            
        return JSONResponse(content={"results": results})
        
    except Exception as e:
        logger.error(f"Error checking product tables: {e}")
        return JSONResponse(
            status_code=500,
            content={"results": {
                "error": f"Failed to check product tables: {str(e)}",
                "success": False,
                "bot_blocked": False
            }}
        )

# Add a new endpoint to compare HTTP vs browser checking methods
@app.post("/api/compare_detection_methods")
async def compare_detection_methods(
    urls: list = Body(..., description="List of URLs to check using both methods"),
    timeout: Optional[int] = Body(None, description="Timeout for checks in seconds")
):
    """
    Check the specified URLs using both HTTP and browser automation methods,
    and compare the results.
    
    Args:
        urls: List of URLs to check
        timeout: Timeout for each check in seconds
        
    Returns:
        dict: Comparison of detection results for each URL
    """
    try:
        if not urls:
            return JSONResponse(
                status_code=400,
                content={"error": "No URLs provided"}
            )
            
        results = {}
        for url in urls:
            try:
                # Log the URL we're checking
                logger.info(f"Comparing detection methods for URL: {url}")
                
                # Handle test domains differently depending on mode
                # In production, partly-products-showcase.lovable.app should NOT be considered a test domain
                if config.mode == 'production':
                    is_test_domain = ('localhost:5001' in url or '127.0.0.1:5001' in url)
                else:
                    # In development mode, also treat partly-products-showcase.lovable.app as a test domain
                    is_test_domain = ('partly-products-showcase.lovable.app' in url or 
                                    'localhost:5001' in url or 
                                    '127.0.0.1:5001' in url)
                               
                if (config.mode == 'development' and is_test_domain):
                    
                    simulated_result = {
                        'found': True, 
                        'class_name': 'product-table productListContainer',
                        'detection_method': 'simulated',
                        'is_test_domain': True,
                        'bot_blocked': False  # Always false for simulated results
                    }
                    
                    results[url] = {
                        'http': simulated_result,
                        'browser': simulated_result,
                        'is_test_domain': True
                    }
                    
                else:
                    # First, try HTTP method
                    http_result = email_qa_enhanced.check_for_product_tables(url, timeout=timeout)
                    
                    # Then try browser method if available
                    if BROWSER_AUTOMATION_AVAILABLE:
                        try:
                            browser_result = browser_check(url, timeout=timeout)
                        except Exception as browser_error:
                            # Check for bot protection indicators in error message
                            error_message = str(browser_error).lower()
                            bot_protection_indicators = [
                                'captcha', 'security', 'cloudflare', 'challenge', 'blocked', 
                                'denied', 'bot', 'protection', 'automated', 'detection'
                            ]
                            
                            bot_detected = any(indicator in error_message for indicator in bot_protection_indicators)
                            
                            if bot_detected:
                                logger.warning(f"Possible bot protection detected in browser error: {error_message}")
                            
                            browser_result = {
                                'found': False,
                                'error': f"Browser automation error: {str(browser_error)}",
                                'detection_method': 'browser_error',
                                'bot_blocked': bot_detected
                            }
                    else:
                        browser_result = {
                            'found': False,
                            'error': "Browser automation not available",
                            'detection_method': 'unavailable',
                            'bot_blocked': False  # No bot blocking since browser automation isn't even attempted
                        }
                    
                    # If text analysis is available, include it in the comparison
                    if TEXT_ANALYSIS_AVAILABLE:
                        try:
                            text_result = check_for_product_tables_with_text_analysis(url)
                        except Exception as text_error:
                            # Check for bot protection indicators in error message
                            error_message = str(text_error).lower()
                            bot_protection_indicators = [
                                'captcha', 'security', 'cloudflare', 'challenge', 'blocked', 
                                'denied', 'bot', 'protection', 'automated', 'detection'
                            ]
                            
                            bot_detected = any(indicator in error_message for indicator in bot_protection_indicators)
                            
                            if bot_detected:
                                logger.warning(f"Possible bot protection detected in text analysis error: {error_message}")
                            
                            text_result = {
                                'found': False,
                                'error': f"Text analysis error: {str(text_error)}",
                                'detection_method': 'text_analysis_error',
                                'bot_blocked': bot_detected
                            }
                            
                        # Add text analysis result to the comparison
                        comparison_result = {
                            'http': http_result,
                            'browser': browser_result,
                            'text_analysis': text_result,
                            'agreement': {
                                'http_browser': http_result.get('found') == browser_result.get('found'),
                                'http_text': http_result.get('found') == text_result.get('found'),
                                'browser_text': browser_result.get('found') == text_result.get('found'),
                                'all_agree': (http_result.get('found') == browser_result.get('found') == text_result.get('found'))
                            }
                        }
                        
                        # Determine recommended method based on majority vote
                        detection_count = sum([
                            1 if http_result.get('found') else 0,
                            1 if browser_result.get('found') else 0,
                            1 if text_result.get('found') else 0
                        ])
                        
                        if detection_count >= 2:
                            # At least 2 methods found a product table - positive result
                            comparison_result['recommended'] = 'majority_vote_positive'
                        elif detection_count == 0:
                            # No method found a product table - negative result
                            comparison_result['recommended'] = 'majority_vote_negative'
                        else:
                            # Only one method found a product table - use the most reliable method
                            if browser_result.get('found'):
                                comparison_result['recommended'] = 'browser_only'
                            elif http_result.get('found'):
                                comparison_result['recommended'] = 'http_only'
                            elif text_result.get('found'):
                                comparison_result['recommended'] = 'text_analysis_only'
                            else:
                                comparison_result['recommended'] = None
                    else:
                        # Just HTTP and browser comparison if text analysis isn't available
                        comparison_result = {
                            'http': http_result,
                            'browser': browser_result,
                            'agreement': http_result.get('found') == browser_result.get('found'),
                            'recommended': 'browser' if browser_result.get('found') else ('http' if http_result.get('found') else None)
                        }
                        
                    results[url] = comparison_result
            
            except Exception as url_error:
                logger.error(f"Error comparing methods for URL {url}: {str(url_error)}")
                # Check for bot protection indicators in error message
                error_message = str(url_error).lower()
                bot_protection_indicators = [
                    'captcha', 'security', 'cloudflare', 'challenge', 'blocked', 
                    'denied', 'bot', 'protection', 'automated', 'detection'
                ]
                
                bot_detected = any(indicator in error_message for indicator in bot_protection_indicators)
                
                if bot_detected:
                    logger.warning(f"Possible bot protection detected in URL error: {error_message}")
                
                results[url] = {
                    'error': f"Error processing URL: {str(url_error)}",
                    'success': False,
                    'bot_blocked': bot_detected
                }
                
        return JSONResponse(content={"results": results})
        
    except Exception as e:
        logger.error(f"Error comparing detection methods: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"results": {
                "error": f"Failed to compare detection methods: {str(e)}",
                "success": False,
                "bot_blocked": False
            }}
        )

@app.post("/run-qa")
async def run_qa(
    email: UploadFile = File(...), 
    requirements: UploadFile = File(...),
    force_production: Optional[bool] = Query(False, description="Force production mode for this request"),
    force_development: Optional[bool] = Query(False, description="Force development mode for this request"),
    check_product_tables: Optional[bool] = Query(False, description="Whether to check for product tables"),
    product_table_timeout: Optional[int] = Query(None, description="Timeout for product table checks in seconds"),
    prefer_browser: Optional[bool] = Query(True, description="Prefer browser automation for product table checks")
):
    """
    Run QA validation on the uploaded email HTML against the provided requirements JSON.
    
    Args:
        email: HTML file of the email to validate
        requirements: JSON file containing validation requirements
        force_production: If True, temporarily run in production mode
        force_development: If True, temporarily run in development mode
        check_product_tables: If True, check for product tables (may slow down validation)
        product_table_timeout: Timeout for product table checks in seconds
    
    Returns:
        dict: Validation results
    """
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    
    # Save current mode to restore it later
    original_mode = config.mode
    
    try:
        # Handle mode forcing
        if force_production and force_development:
            return JSONResponse(
                status_code=400,
                content={"results": {
                    "error": "Cannot force both production and development modes simultaneously",
                    "success": False,
                    "bot_blocked": False
                }}
            )
        elif force_production:
            logger.info("Forcing production mode for this request")
            config.set_mode("production")
        elif force_development:
            logger.info("Forcing development mode for this request")
            config.set_mode("development")
        
        # Save uploaded files
        email_path = os.path.join(temp_dir, "email.html")
        req_path = os.path.join(temp_dir, "requirements.json")
        
        with open(email_path, "wb") as buffer:
            shutil.copyfileobj(email.file, buffer)
        
        with open(req_path, "wb") as buffer:
            shutil.copyfileobj(requirements.file, buffer)
        
        # Run validation with product table detection parameters
        # Convert check_product_tables to a boolean to handle the None case
        check_tables = bool(check_product_tables)
        # Load requirements first so we can include them in the results
        with open(req_path, "r") as f:
            requirements_json = json.load(f)
            
        # Log the requirements JSON for debugging
        logger.info(f"Requirements JSON: {json.dumps(requirements_json, indent=2)}")
        
        results = validate_email(
            email_path, 
            req_path,
            check_product_tables=check_tables,
            product_table_timeout=product_table_timeout
        )
        
        # Add requirements to results
        results["requirements"] = requirements_json
        
        # Add mode and product table detection info to results
        if force_production:
            results["forced_mode"] = "production"
        elif force_development:
            results["forced_mode"] = "development"
            
        # Add product table detection status to results
        results["product_tables_checked"] = check_tables
        if product_table_timeout:
            results["product_table_timeout"] = product_table_timeout
        
        # Standardize response format with results wrapper for consistency
        # This ensures all API responses have the same structure, which makes frontend handling easier
        return JSONResponse(content={"results": results})
    
    except Exception as e:
        error_detail = f"QA validation failed: {str(e)}"
        logger.error(error_detail)
        return JSONResponse(
            status_code=500,
            content={"results": {"error": error_detail, "success": False, "bot_blocked": False}}
        )
    
    finally:
        # Restore original mode if it was changed
        if force_production or force_development:
            config.set_mode(original_mode)
        
        # Clean up temporary files
        shutil.rmtree(temp_dir)