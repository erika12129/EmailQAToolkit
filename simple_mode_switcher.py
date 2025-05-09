"""
Simple mode-switching implementation for the Email QA System.
Enhanced with hybrid browser automation for better product table detection.
"""

import os
import shutil
import tempfile
import logging
import json
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional, List, Dict, Any
import email_qa_enhanced
from email_qa_enhanced import validate_email
from runtime_config import config

# Import browser automation module
# Define a fallback function in case the real one isn't available
def browser_check_fallback(url, timeout=None):
    """Fallback function when browser automation is not available."""
    return {
        'found': False,
        'error': "Browser automation not available",
        'detection_method': 'unavailable'
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

# Try to import the real browser check function
try:
    # First try to import the Selenium implementation
    try:
        from selenium_automation import check_for_product_tables_selenium_sync as browser_check
        BROWSER_AUTOMATION_AVAILABLE = True
        logging.info("Selenium browser automation module loaded successfully")
    except ImportError:
        # Fall back to Playwright if Selenium is not available
        from browser_automation import check_for_product_tables_sync as browser_check
        BROWSER_AUTOMATION_AVAILABLE = True
        logging.info("Playwright browser automation module loaded successfully")
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
    return JSONResponse(content={
        "mode": config.mode,
        "enable_test_redirects": config.enable_test_redirects,
        "product_table_timeout": config.product_table_timeout,
        "request_timeout": config.request_timeout,
        "max_retries": config.max_retries,
        "test_domains": config.test_domains
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
@app.get("/api/check_simple") # Simple GET endpoint for testing connectivity
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
                    logger.info(f"Using simulated success response for test domain in development mode: {url}")
                    # For test domains in development mode, return a simulated positive result
                    results[url] = {
                        'found': True, 
                        'class_name': 'product-table productListContainer',
                        'detection_method': 'simulated',
                        'is_test_domain': True
                    }
                # In production mode for partly-products-showcase.lovable.app, use REAL detection
                elif ('partly-products-showcase.lovable.app' in url):
                    logger.info(f"Using REAL detection for partly-products-showcase domain in production mode: {url}")
                    
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
                    http_result['detection_method'] = 'http_production'
                    
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
                            
                            # If browser found something, use that result
                            if browser_result.get('found', False):
                                logger.info(f"Browser automation found product tables for {url} in production")
                                results[url] = browser_result
                        except Exception as e:
                            logger.warning(f"Browser automation failed in production mode for {url}: {str(e)}")
                        
                    # Try text analysis as a last resort if nothing was found
                    if not results[url].get('found', False) and TEXT_ANALYSIS_AVAILABLE:
                        try:
                            logger.info(f"Trying text analysis as last resort for {url}")
                            text_result = check_for_product_tables_with_text_analysis(url)
                            text_result['detection_method'] = 'text_analysis_production'
                            
                            # Only use text analysis if it found something
                            if text_result.get('found', False):
                                logger.info(f"Text analysis found product tables for {url}")
                                results[url] = text_result
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
                    else:
                        # Browser automation is not available, use direct HTTP check
                        logger.info(f"Browser automation not available, using direct HTTP check for {url}")
                        result = email_qa_enhanced.check_for_product_tables(url, timeout=timeout)
                        
                        # Add additional context to the result to show we used direct HTTP
                        if 'detection_method' not in result:
                            result['detection_method'] = 'direct_http'
                    
                    logger.info(f"Product table check result for {url}: {result}")
                    results[url] = result
            except Exception as url_error:
                # Handle errors for individual URLs separately
                logger.error(f"Error checking product table for URL {url}: {str(url_error)}")
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
            content={"error": f"Failed to check product tables: {str(e)}"}
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
                        'is_test_domain': True
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
                            browser_result = {
                                'found': False,
                                'error': f"Browser automation error: {str(browser_error)}",
                                'detection_method': 'browser_error'
                            }
                    else:
                        browser_result = {
                            'found': False,
                            'error': "Browser automation not available",
                            'detection_method': 'unavailable'
                        }
                    
                    # If text analysis is available, include it in the comparison
                    if TEXT_ANALYSIS_AVAILABLE:
                        try:
                            text_result = check_for_product_tables_with_text_analysis(url)
                        except Exception as text_error:
                            text_result = {
                                'found': False,
                                'error': f"Text analysis error: {str(text_error)}",
                                'detection_method': 'text_analysis_error'
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
                results[url] = {
                    'error': f"Error processing URL: {str(url_error)}"
                }
                
        return JSONResponse(content={"results": results})
        
    except Exception as e:
        logger.error(f"Error comparing detection methods: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to compare detection methods: {str(e)}"}
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
                content={"error": "Cannot force both production and development modes simultaneously"}
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
        
        # Explicitly return as JSON with appropriate headers
        return JSONResponse(content=results)
    
    except Exception as e:
        error_detail = f"QA validation failed: {str(e)}"
        logger.error(error_detail)
        return JSONResponse(
            status_code=500,
            content={"detail": error_detail}
        )
    
    finally:
        # Restore original mode if it was changed
        if force_production or force_development:
            config.set_mode(original_mode)
        
        # Clean up temporary files
        shutil.rmtree(temp_dir)