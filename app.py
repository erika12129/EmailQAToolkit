"""
Web server for Email QA System with improved accessibility.
Serves static files and provides API endpoints.
"""
import os
import uvicorn
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from typing import Optional, List, Dict, Any
import shutil
import tempfile
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import email_qa_enhanced
import email_qa_enhanced
from email_qa_enhanced import validate_email

# Create FastAPI app
app = FastAPI(title="Email QA Automation API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/attached_assets", StaticFiles(directory="attached_assets"), name="attached_assets")

# Import the runtime configuration
from runtime_config import config, RuntimeConfig

# Import browser automation modules if available
try:
    import browser_automation
    BROWSER_AUTOMATION_AVAILABLE = True
    logger.info("Browser automation module imported successfully")
except ImportError:
    BROWSER_AUTOMATION_AVAILABLE = False
    logger.warning("Browser automation module not available")

try:
    import selenium_automation
    SELENIUM_AUTOMATION_AVAILABLE = True
    logger.info("Selenium automation module imported successfully")
except ImportError:
    SELENIUM_AUTOMATION_AVAILABLE = False
    logger.warning("Selenium automation module not available")

# Add config endpoint for frontend usage
@app.get("/config")
async def get_config():
    """Get current configuration settings for frontend."""
    logger.info(f"Serving config endpoint, mode={config.mode}")
    runtime_config = RuntimeConfig()
    # Get config data in a safer way
    mode = runtime_config.mode if hasattr(runtime_config, "mode") else "production"
    test_domains = []
    
    # Try accessing config properties safely
    try:
        test_redirects = config.enable_test_redirects() if callable(getattr(config, "enable_test_redirects", None)) else False
        timeout = config.request_timeout() if callable(getattr(config, "request_timeout", None)) else 10
        retries = config.max_retries() if callable(getattr(config, "max_retries", None)) else 3
        
        if callable(getattr(config, "test_domains", None)):
            domains = config.test_domains()
            if hasattr(domains, "keys"):
                test_domains = list(domains.keys())
    except Exception as e:
        logger.error(f"Error accessing config: {str(e)}")
        test_redirects = False
        timeout = 10
        retries = 3
    
    return JSONResponse(content={
        "mode": mode,
        "enable_test_redirects": test_redirects,
        "request_timeout": timeout,
        "max_retries": retries,
        "test_domains": test_domains
    })

@app.get("/")
async def read_root():
    """Serve the frontend application."""
    # Get runtime config instance
    runtime_config = RuntimeConfig()
    
    # Load HTML content
    with open("static/index.html", "r") as f:
        html_content = f.read()
    
    # Set application mode in the HTML based on runtime config
    is_prod_mode = runtime_config.is_production()
    mode = "production" if is_prod_mode else "development"
    
    # Add or update the data-mode attribute
    if "<body data-mode=" in html_content:
        # If data-mode already exists, update it
        html_content = html_content.replace('<body data-mode="production">', f'<body data-mode="{mode}">')
        html_content = html_content.replace('<body data-mode="development">', f'<body data-mode="{mode}">')
    else:
        # Otherwise add the attribute
        html_content = html_content.replace('<body>', f'<body data-mode="{mode}">')
    
    # Log the mode for debugging
    logger.info(f"Serving frontend with mode: {mode}")
    
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/set-mode/{mode}")
async def set_mode(mode: str):
    """Switch between development and production modes."""
    # Get runtime config instance
    runtime_config = RuntimeConfig()
    
    if mode not in ["development", "production"]:
        raise HTTPException(status_code=400, detail="Invalid mode. Must be 'development' or 'production'")
    
    # Set the mode
    runtime_config.set_mode(mode)
    
    # Return success
    return JSONResponse(content={"success": True, "mode": mode})

@app.get("/assets/{file_path:path}")
async def serve_asset(file_path: str):
    """Serve attached assets with proper content type."""
    asset_path = os.path.join("attached_assets", file_path)
    
    if not os.path.exists(asset_path):
        raise HTTPException(status_code=404, detail=f"Asset not found: {file_path}")
    
    return FileResponse(asset_path)

@app.post("/run-qa")
async def run_qa(
    email: UploadFile = File(...), 
    requirements: UploadFile = File(...),
    check_product_tables: Optional[bool] = Query(False, description="Whether to check for product tables"),
    product_table_timeout: Optional[int] = Query(None, description="Timeout for product table checks in seconds")
):
    """
    Run QA validation on the uploaded email HTML against the provided requirements JSON.
    
    Args:
        email: HTML file of the email to validate
        requirements: JSON file containing validation requirements
        check_product_tables: If True, check for product tables (may slow down validation)
        product_table_timeout: Timeout for product table checks in seconds
    
    Returns:
        dict: Validation results
    """
    # Create temporary files to store the uploads
    email_fd, email_path = tempfile.mkstemp(suffix=".html")
    req_fd, req_path = tempfile.mkstemp(suffix=".json")
    
    try:
        # Save the uploaded files
        with open(email_path, "wb") as f:
            f.write(await email.read())
        
        with open(req_path, "wb") as f:
            f.write(await requirements.read())
        
        # Validate the email
        results = validate_email(
            email_path, 
            req_path, 
            check_product_tables=check_product_tables,
            product_table_timeout=product_table_timeout
        )
        
        # Return the validation results
        return JSONResponse(content=results)
        
    except Exception as e:
        logger.error(f"Error in run_qa: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing files: {str(e)}")
    
    finally:
        # Clean up the temporary files
        os.close(email_fd)
        os.close(req_fd)
        os.remove(email_path)
        os.remove(req_path)

@app.post("/check-product-tables")
async def check_product_tables(
    urls: List[str] = Body(..., description="List of URLs to check for product tables"),
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
    logger.info(f"Checking {len(urls)} URLs for product tables")
    
    results = {}
    for url in urls:
        logger.info(f"Checking URL: {url}")
        
        try:
            # Try browser automation first if available in production mode
            if config.is_production() and BROWSER_AUTOMATION_AVAILABLE:
                logger.info(f"Using browser automation for {url}")
                result = browser_automation.check_for_product_tables_sync(url, timeout)
                result['detection_method'] = 'browser'
                
                # If browser automation reports bot blocking, we'll keep that result
                if result.get('bot_blocked', False):
                    logger.warning(f"Bot blocking detected for {url} with browser automation")
                    results[url] = result
                    continue
                    
                # If browser automation found something or errored in a specific way, use that result
                if result.get('found', False) or result.get('error_message'):
                    results[url] = result
                    continue
                    
                # If browser automation didn't find anything, fall back to HTTP check
                logger.info(f"Using HTTP fallback after browser check for {url}")
                result = email_qa_enhanced.check_for_product_tables(url, timeout=timeout)
                result['detection_method'] = 'http_fallback'
                results[url] = result
                
            # Try Selenium as a second fallback in production mode
            elif config.is_production() and SELENIUM_AUTOMATION_AVAILABLE:
                logger.info(f"Using Selenium automation for {url}")
                
                try:
                    result = selenium_automation.check_for_product_tables_selenium_sync(url, timeout)
                    result['detection_method'] = 'selenium'
                    
                    # If Selenium reports bot blocking, keep that result
                    if result.get('bot_blocked', False):
                        logger.warning(f"Bot blocking detected for {url} with Selenium")
                        results[url] = result
                        continue
                        
                    # If Selenium found something or errored specifically, use that result
                    if result.get('found', False) or result.get('error_message'):
                        results[url] = result
                        continue
                        
                except Exception as e:
                    logger.error(f"Selenium error for {url}: {str(e)}")
                    
                # Fall back to HTTP check
                logger.info(f"Using HTTP fallback after Selenium error for {url}")
                result = email_qa_enhanced.check_for_product_tables(url, timeout=timeout)
                result['detection_method'] = 'http_fallback_after_error'
                results[url] = result
                
            else:
                # Use direct HTTP check
                logger.info(f"Using direct HTTP check for {url}")
                result = email_qa_enhanced.check_for_product_tables(url, timeout=timeout)
                result['detection_method'] = 'direct_http'
                results[url] = result
                
        except Exception as e:
            logger.error(f"Error checking {url}: {str(e)}")
            results[url] = {
                'found': False,
                'error': f"Error checking URL: {str(e)}",
                'detection_method': 'error'
            }
    
    logger.info(f"Completed checking {len(urls)} URLs for product tables")
    return JSONResponse(content=results)

# Add additional routes for diagnostics (helpful for troubleshooting)
@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy"}

@app.get("/browser-status")
async def browser_status():
    """Check browser automation availability."""
    browser_status = {
        "browser_automation_available": BROWSER_AUTOMATION_AVAILABLE,
        "selenium_automation_available": SELENIUM_AUTOMATION_AVAILABLE
    }
    
    # Add more detailed info if available
    if SELENIUM_AUTOMATION_AVAILABLE:
        browser_status["selenium_browsers"] = {
            "chrome_available": selenium_automation.CHROME_AVAILABLE,
            "firefox_available": selenium_automation.FIREFOX_AVAILABLE
        }
    
    return browser_status

# For standalone execution
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)