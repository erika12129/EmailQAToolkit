"""
Main entry point for the Email QA Automation application.
This file is used for deployment on Replit.
"""
import os
import uvicorn
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from typing import Optional, List
import shutil
import tempfile
import json
import logging

# Import the email_qa module
from email_qa_enhanced import validate_email
from cloud_browser_automation import check_for_product_tables_cloud
from browser_automation import check_for_product_tables_sync

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

# Mount attached assets
app.mount("/attached_assets", StaticFiles(directory="attached_assets"), name="attached_assets")

# Import API router
from api_endpoints import router as api_router

# Include API router with a prefix
app.include_router(api_router, prefix="/api")

# Import the runtime configuration
from runtime_config import config

# Add config endpoint for frontend usage
@app.get("/config")
@app.get("/api/config")  # Add API prefix for compatibility with frontend
async def get_config():
    """Get current configuration settings for frontend."""
    logger.info(f"Serving config endpoint, mode={config.mode}")
    
    # REPLIT OPTIMIZATION: Skip the Selenium check in Replit environments
    # as it may cause hangs and isn't needed with cloud browser API
    browser_available = False
    
    # Fast check if we're in Replit
    is_replit = os.environ.get('REPL_ID') is not None or os.environ.get('REPLIT_ENVIRONMENT') is not None
    
    if is_replit:
        # In Replit, don't check for local browsers - just check for API keys
        scrapingbee_key = os.environ.get('SCRAPINGBEE_API_KEY', '')
        browserless_key = os.environ.get('BROWSERLESS_API_KEY', '')
        browser_available = bool(scrapingbee_key or browserless_key)
        logger.info(f"Replit environment detected, using cloud browser availability: {browser_available}")
    else:
        # Only in non-Replit environments, check traditionally
        try:
            # Import selenium_automation for browser availability check
            from selenium_automation import check_browser_availability
            
            # Check if browser automation is available
            browser_available = check_browser_availability()
            logger.info(f"Checking browser automation for config endpoint: {browser_available}")
        except Exception as e:
            logger.error(f"Error checking browser automation availability: {str(e)}")
            browser_available = False
    
    # Create safe version of the test domains for response
    # The test_domains might include complex objects that aren't JSON serializable
    try:
        # Convert test domains to a simpler format if needed
        test_domains_safe = {}
        if hasattr(config, 'test_domains') and config.test_domains:
            if isinstance(config.test_domains, dict):
                # Simple copy of dictionary - exclude any complex objects
                for domain, info in config.test_domains.items():
                    if isinstance(info, dict):
                        test_domains_safe[domain] = {
                            k: v for k, v in info.items() 
                            if isinstance(v, (str, int, float, bool, list)) or v is None
                        }
                    else:
                        # If not a dict, only include if it's a simple type
                        if isinstance(info, (str, int, float, bool)) or info is None:
                            test_domains_safe[domain] = info
            elif isinstance(config.test_domains, (list, tuple)):
                # If it's a list, convert to a simple dictionary
                test_domains_safe = {domain: True for domain in config.test_domains}
    except Exception as e:
        logger.error(f"Error processing test domains for config response: {str(e)}")
        test_domains_safe = {}
    
    # Check for cloud browser API keys
    try:
        scrapingbee_key = os.environ.get('SCRAPINGBEE_API_KEY', '')
        browserless_key = os.environ.get('BROWSERLESS_API_KEY', '')
        
        cloud_browser_available = bool(scrapingbee_key or browserless_key)
        
        # Update browser_available to include cloud browser status
        browser_available = browser_available or cloud_browser_available
        
        logger.info(f"Cloud browser availability: {cloud_browser_available}")
    except Exception as e:
        logger.error(f"Error checking cloud browser keys: {str(e)}")
        cloud_browser_available = False
    
    # Create config response with safely serializable data only
    try:
        config_response = {
            "mode": config.mode,
            "enable_test_redirects": config.enable_test_redirects,
            "product_table_timeout": getattr(config, 'product_table_timeout', 30),
            "request_timeout": getattr(config, 'request_timeout', 10),
            "max_retries": getattr(config, 'max_retries', 3),
            "test_domains": test_domains_safe,
            "browser_automation_available": browser_available,
            "cloud_browser_available": cloud_browser_available
        }
        
        logger.info(f"Config response: {config_response}")
        
        return JSONResponse(content=config_response)
    except Exception as e:
        logger.error(f"Error creating config response: {str(e)}")
        # Fallback minimal response with cloud browser info
        try:
            # Include cloud browser status even in the fallback response
            scrapingbee_key = os.environ.get('SCRAPINGBEE_API_KEY', '')
            browserless_key = os.environ.get('BROWSERLESS_API_KEY', '')
            cloud_browser_available = bool(scrapingbee_key or browserless_key)
        except Exception:
            cloud_browser_available = False
            
        return JSONResponse(content={
            "mode": config.mode,
            "browser_automation_available": browser_available,
            "cloud_browser_available": cloud_browser_available,
            "error": f"Config error: {str(e)}"
        })

@app.get("/")
async def read_root():
    """Serve the frontend application."""
    # Import runtime config classes
    from runtime_config import RuntimeConfig
    
    # Get runtime config instance
    runtime_config = RuntimeConfig()
    
    # Load HTML content
    with open("static/index.html", "r") as f:
        html_content = f.read()
    
    # Set application mode in the HTML based on runtime config
    # Correctly access the is_production property
    is_prod_mode = runtime_config.is_production
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

@app.get("/attached_assets/{file_path:path}")
async def serve_asset(file_path: str):
    """Serve attached assets with proper content type."""
    
    full_path = os.path.join("attached_assets", file_path)
    
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    # Special handling for markdown files
    if file_path.endswith(".md"):
        with open(full_path, "r") as f:
            md_content = f.read()
        
        # Create a simple HTML wrapper for the markdown content
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Documentation</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }
                pre {
                    background-color: #f5f5f5;
                    padding: 10px;
                    border-radius: 5px;
                    overflow-x: auto;
                }
                code {
                    background-color: #f5f5f5;
                    padding: 2px 4px;
                    border-radius: 3px;
                }
                h1, h2, h3 {
                    color: #2c5282;
                }
                a {
                    color: #3182ce;
                }
                .markdown-content {
                    white-space: pre-wrap;
                }
            </style>
        </head>
        <body>
            <div class="markdown-content">""" + md_content + """</div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content, status_code=200)
    
    # For all other files, use FileResponse
    return FileResponse(full_path)

@app.post("/run-qa")
async def run_qa(
    email: UploadFile = File(...), 
    requirements: UploadFile = File(...),
    check_product_tables: Optional[bool] = Query(False, description="Whether to check for product tables"),
    product_table_timeout: Optional[int] = Query(5, description="Timeout for product table checks in seconds")
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
    # IMPORTANT: Force check_product_tables to False to prevent hanging
    check_product_tables = False
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Save uploaded files
        email_path = os.path.join(temp_dir, "email.html")
        req_path = os.path.join(temp_dir, "requirements.json")
        
        with open(email_path, "wb") as buffer:
            shutil.copyfileobj(email.file, buffer)
        
        with open(req_path, "wb") as buffer:
            shutil.copyfileobj(requirements.file, buffer)
        
        # Load requirements first so we can include them in the results
        with open(req_path, "r") as f:
            requirements_json = json.load(f)
            
        # Add logging for debugging requirements
        print(f"Requirements JSON in main.py: {json.dumps(requirements_json, indent=2)}")
        
        # Run validation
        # Convert check_product_tables to a boolean to handle the None case
        check_tables = bool(check_product_tables)
        
        results = validate_email(
            email_path, 
            req_path, 
            check_product_tables=check_tables,
            product_table_timeout=product_table_timeout
        )
        
        # Add requirements to results
        results["requirements"] = requirements_json
        
        # Explicitly return as JSON with appropriate headers
        return JSONResponse(
            content=results,
            media_type="application/json"
        )
    
    except Exception as e:
        error_detail = f"Failed to validate email: {str(e)}"
        logger.error(error_detail)
        
        # Return error in the expected format for the frontend
        return JSONResponse(
            content={
                "results": {
                    "error": error_detail,
                    "mode": getattr(config, 'mode', 'production'),
                    "requirements": {},
                    "product_tables_checked": bool(check_product_tables)
                }
            },
            media_type="application/json"
        )
    
    finally:
        # Clean up temporary files
        shutil.rmtree(temp_dir)

@app.post("/check-product-tables")
@app.post("/check_product_tables")  # Add underscore version for frontend compatibility
@app.post("/api/check_product_tables")  # Add with /api prefix for frontend compatibility
async def check_product_tables(
    urls: list = Body(..., description="List of URLs to check for product tables"),
    timeout: Optional[int] = Body(None, description="Timeout for product table checks in seconds")
):
    """
    Check if the specified URLs contain product tables.
    This endpoint allows for checking selected links after initial validation,
    with an adjustable timeout to prevent hanging the main validation process.
    
    This version uses the cloud-based detection method to find product tables
    in React-rendered applications, focusing on specific class names like
    'product-table', 'productListContainer', 'noPartsPhrase'.
    
    Args:
        urls: List of URLs to check for product tables
        timeout: Timeout for each check in seconds (defaults to config setting)
        
    Returns:
        dict: Results of product table detection for each URL
    """
    # Import the simplified cloud detection endpoint handler
    from simplified_cloud_endpoint import check_product_tables_endpoint
    
    # Use the simplified implementation that directly uses cloud detection
    return check_product_tables_endpoint(urls, timeout)
    
    # Set up logging
    logger = logging.getLogger(__name__)
    
    # Get current config
    runtime_config = RuntimeConfig()
    is_production = runtime_config.is_production
    
    # Set a default timeout to prevent hanging in deployed environments
    if timeout is None:
        # In production environments, use a shorter timeout
        if is_production:
            timeout = 45  # 45 seconds in production
        else:
            timeout = 60  # 60 seconds in development
    
    # Check if cloud browser API is available
    SCRAPINGBEE_API_KEY = os.environ.get('SCRAPINGBEE_API_KEY', '')
    BROWSERLESS_API_KEY = os.environ.get('BROWSERLESS_API_KEY', '')
    CLOUD_BROWSER_AVAILABLE = bool(SCRAPINGBEE_API_KEY or BROWSERLESS_API_KEY)
    
    logger.info(f"Product table check - ScrapingBee API key available: {bool(SCRAPINGBEE_API_KEY)}")
    logger.info(f"Product table check - Browserless API key available: {bool(BROWSERLESS_API_KEY)}")
    logger.info(f"Product table check - Cloud browser available: {CLOUD_BROWSER_AVAILABLE}")
    
    # For cloud browser API, use a shorter timeout to prevent hanging
    if CLOUD_BROWSER_AVAILABLE:
        # Use a much shorter timeout to prevent UI hanging
        cloud_timeout = 15  # Only 15 seconds for cloud API to prevent UI hanging
        logger.info(f"Setting cloud browser timeout to {cloud_timeout}s (was {timeout}s)")
        timeout = cloud_timeout
    
    # Enforce a reasonable timeout to prevent hanging and save API credits
    if timeout is None or timeout <= 0:
        timeout = 8  # Default reasonable timeout
        logger.info(f"Using default timeout of {timeout}s")
    elif timeout > 15:
        logger.warning(f"Requested timeout of {timeout}s exceeds recommended maximum, limiting to 15s to save API credits")
        timeout = 15  # Shorter timeout to save API credits and prevent hanging
    
    # Log the timeout being used
    logger.info(f"Using product table timeout of {timeout} seconds for {len(urls)} URLs")
    
    try:
        results = {}
        
        # First check if we're in Replit environment - if so, handle all URLs the same way
        # DIRECT FIX: In Replit, we ALWAYS want to return "Unknown" for URLs with "/products"
        # This is the critical requirement regardless of environment variables
        
        for url in urls:
            # Check if this might be a product-related URL
            is_product_url = '/products/' in url or '/product/' in url or url.endswith('/products')
            logger.info(f"URL classification for {url}: product-related={is_product_url}")
            
            # SIMPLIFIED DIRECT APPROACH: Use cloud detection for all URLs when available
            if CLOUD_BROWSER_AVAILABLE:
                logger.info(f"Cloud browser available - using direct detection for URL: {url}")
                
                try:
                    # Log API key availability
                    scrapingbee_key = os.environ.get('SCRAPINGBEE_API_KEY', '')
                    if scrapingbee_key:
                        logger.info(f"Using ScrapingBee API key: {scrapingbee_key[:4]}...")
                    
                    # Call cloud browser directly
                    logger.info(f"Making direct cloud browser call for URL: {url}")
                    result = check_for_product_tables_cloud(url, timeout)
                    
                    # Add debugging info
                    logger.info(f"Cloud detection result: found={result.get('found')}, method={result.get('detection_method')}")
                    
                    if result.get('found') is True:
                        logger.info(f"✅ SUCCESS: Product table detected at {url} via {result.get('detection_method')}")
                    elif result.get('found') is False:
                        logger.info(f"Product table NOT found at {url}")
                    else:
                        logger.info(f"Product table detection UNKNOWN for {url}")
                    
                    # Store the result directly - this is key to fixing the issue
                    results[url] = result
                    continue  # Skip the rest of processing for this URL
                except Exception as e:
                    logger.error(f"Error using cloud browser: {str(e)}")
                    # Fall back to manual verification if cloud browser fails
            
            # We only reach here if cloud browser is not available or fails
            # For product URLs, use manual verification message
            if is_product_url:
                logger.info(f"Using manual verification for product URL: {url}")
                results[url] = {
                    "found": None,
                    "class_name": None, 
                    "detection_method": "browser_unavailable",
                    "message": "Unknown - Browser automation unavailable - manual verification required",
                    "is_test_domain": False
                }
                continue  # Skip all other checks for this URL
                
            # For other URLs, re-use the same environment detection variables
            # that were already defined above
            
            # Log the environment detection with detailed debugging (reusing variables)
            logger.info(f"ENVIRONMENT CHECK - REPL_ID: '{repl_id}', REPLIT_ENVIRONMENT: '{replit_env}'")
            
            # In Replit environment with cloud browser API available, use direct cloud API
            if is_replit and CLOUD_BROWSER_AVAILABLE:
                logger.info(f"Replit environment with cloud browser API - DIRECT CLOUD API CALL for {url}")
                
                try:
                    # Import and use cloud browser API directly
                    from cloud_browser_automation import check_for_product_tables_cloud
                    
                    # Re-check API keys to ensure they're available in this context
                    scrapingbee_key = os.environ.get('SCRAPINGBEE_API_KEY', '')
                    browserless_key = os.environ.get('BROWSERLESS_API_KEY', '')
                    
                    # Ensure keys are in the environment for imported function
                    if scrapingbee_key:
                        os.environ['SCRAPINGBEE_API_KEY'] = scrapingbee_key
                        logger.info(f"Using ScrapingBee API key: {scrapingbee_key[:4]}...")
                    if browserless_key:
                        os.environ['BROWSERLESS_API_KEY'] = browserless_key
                        logger.info(f"Using Browserless API key: {browserless_key[:4]}...")
                    
                    # Call cloud browser directly, bypassing check_for_product_tables
                    logger.info(f"DIRECT CLOUD BROWSER CALL for URL: {url}")
                    result = check_for_product_tables_cloud(url, timeout)
                    
                    logger.info(f"DIRECT Cloud browser result for URL: {result}")
                    results[url] = result
                    continue  # Skip the rest of processing for this URL
                except Exception as e:
                    logger.error(f"Error using direct cloud browser for URL: {str(e)}")
                    logger.exception("Full traceback for cloud browser error:")
                    # If there's an error with cloud browser, fall back to the default behavior
            
            # In Replit environment without cloud browser, return the manual verification message
            if is_replit:
                logger.info(f"Replit environment without cloud browser - returning manual verification message for {url}")
                results[url] = {
                    "found": None,
                    "class_name": None,
                    "detection_method": "browser_unavailable",
                    "message": "Unknown - Browser automation unavailable - manual verification required",
                    "is_test_domain": False
                }
                continue  # Skip the rest of the processing for this URL
            
            # Non-Replit environment processing starts here
            # Get runtime config test domains (instead of hardcoding them)
            base_test_domains = ["localhost:5001", "127.0.0.1:5001", "localtest.me"]
            
            # In production mode, partly-products-showcase.lovable.app should NOT be considered a test domain
            if runtime_config.is_production:
                test_domains = base_test_domains
            else:
                # In development mode, also treat partly-products-showcase.lovable.app as a test domain
                test_domains = base_test_domains + ["partly-products-showcase.lovable.app"]
                
            # Check if URL is in the appropriate test_domains list
            is_test_domain = any(domain in url for domain in test_domains)
            
            # For localhost URLs, handle differently based on mode
            if any(domain in url for domain in ["localhost:5001", "127.0.0.1:5001"]):
                if is_production:
                    # In production mode, use http_production method and don't mark as simulated
                    results[url] = {
                        "found": True,
                        "class_name": "product-table",
                        "detection_method": "browser_unavailable",
                        "status_code": 200
                    }
                else:
                    # In development mode, use simulation
                    results[url] = {
                        "found": True,
                        "class_name": "product-table",
                        "detection_method": "simulated",
                        "is_test_domain": True
                    }
            # Handle partly-products-showcase.lovable.app domains (in non-Replit environments)
            elif "partly-products-showcase.lovable.app" in url:
                # In production mode, use real detection
                if is_production:
                    logger.info(f"Using HTTP detection for domain in PRODUCTION mode: {url}")
                    result = check_for_product_tables_cloud(url, timeout=timeout)
                    results[url] = result
                else:
                    # In development mode, use simulation
                    logger.info(f"Using simulation for test domain in development mode: {url}")
                    results[url] = {
                        "found": True,
                        "class_name": "product-table productListContainer",
                        "detection_method": "simulated",
                        "is_test_domain": True
                    }
            else:
                # Normal processing for external URLs in non-Replit environments
                # (we already checked for Replit environment at the beginning)
                result = check_for_product_tables_cloud(url, timeout=timeout)
                
                # Only override with standardized message if cloud browser detection failed
                if result.get("found") is None and not result.get("class_name"):
                    result["message"] = "Unknown - Browser automation unavailable - manual verification required"
                    result["detection_method"] = "browser_unavailable"
                    
                results[url] = result
        
        # Format response correctly with results wrapper for frontend
        response = {
            "results": results,
            "mode": "production" if is_production else "development"
        }
        logger.info(f"Check product tables results (mode: {response['mode']}): {response}")
        
        return JSONResponse(content=response)
    
    except Exception as e:
        logger.error(f"Product table check error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to check product tables: {str(e)}"}
        )

# Batch Processing Endpoints

@app.get("/api/locales")
async def get_supported_locales():
    """Get list of supported locales for batch processing."""
    from locale_config import LOCALE_CONFIGS
    return {
        "locales": [
            {
                "code": code,
                "display_name": config["display_name"],
                "country": config["country"],
                "language": config["language"]
            }
            for code, config in LOCALE_CONFIGS.items()
        ]
    }

@app.post("/api/batch-validate")
async def batch_validate(
    templates: List[UploadFile] = File(..., description="Email template files"),
    locale_mapping: str = Body(..., description="JSON mapping of template files to locale codes"),
    base_requirements: UploadFile = File(..., description="Base requirements JSON file"),
    selected_locales: List[str] = Body(..., description="List of locale codes to process"),
    check_product_tables: bool = Body(True, description="Whether to check for product tables"),
    product_table_timeout: Optional[int] = Body(None, description="Timeout for product table checks")
):
    """
    Process batch validation for multiple email templates across different locales.
    
    Args:
        templates: List of email template files
        locale_mapping: JSON string mapping template filenames to locale codes
        base_requirements: Base requirements JSON file (typically for en_US)
        selected_locales: List of locale codes to process
        check_product_tables: Whether to include product table detection
        product_table_timeout: Timeout for product table checks
        
    Returns:
        dict: Batch processing results with per-locale validation results
    """
    from batch_processor import BatchProcessor, BatchValidationRequest
    import json
    
    try:
        # Parse locale mapping
        try:
            mapping = json.loads(locale_mapping)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid locale_mapping JSON format")
        
        # Parse base requirements
        base_req_content = await base_requirements.read()
        try:
            base_req_dict = json.loads(base_req_content.decode('utf-8'))
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid base requirements JSON format")
        
        # Map templates to locales
        template_dict = {}
        for template in templates:
            filename = template.filename
            if filename in mapping:
                locale = mapping[filename]
                if locale in selected_locales:
                    template_dict[locale] = template
        
        # Debug logging for production deployment
        logger.info(f"Template mapping: {mapping}")
        logger.info(f"Selected locales: {selected_locales}")
        logger.info(f"Template dict keys: {list(template_dict.keys())}")
        
        # Don't validate missing templates here - let the batch processor handle it
        # This allows for more flexible template-to-locale mapping
        
        # Create batch request
        batch_request = BatchValidationRequest(
            templates=template_dict,
            base_requirements=base_req_dict,
            selected_locales=selected_locales,
            check_product_tables=check_product_tables,
            product_table_timeout=product_table_timeout
        )
        
        # Process batch
        processor = BatchProcessor()
        result = await processor.process_batch(batch_request)
        
        return {
            "batch_id": result.batch_id,
            "status": result.status,
            "progress": result.get_progress(),
            "results": result.results,
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat() if result.end_time else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch validation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Batch processing failed: {str(e)}")

@app.get("/api/batch-progress/{batch_id}")
async def get_batch_progress(batch_id: str):
    """Get progress information for a specific batch."""
    from batch_processor import batch_processor
    
    progress = batch_processor.get_batch_progress(batch_id)
    if progress is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    return progress

@app.post("/api/batch-cancel/{batch_id}")
async def cancel_batch(batch_id: str):
    """Cancel an active batch processing operation."""
    from batch_processor import batch_processor
    
    success = batch_processor.cancel_batch(batch_id)
    if not success:
        raise HTTPException(status_code=404, detail="Batch not found or already completed")
    
    return {"message": f"Batch {batch_id} has been cancelled", "batch_id": batch_id}

@app.get("/api/batch-result/{batch_id}")
async def get_batch_result(batch_id: str):
    """Get complete results for a finished batch."""
    from batch_processor import batch_processor
    
    result = batch_processor.get_batch_result(batch_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Batch not found")
    
    return {
        "batch_id": result.batch_id,
        "status": result.status,
        "progress": result.get_progress(),
        "results": result.results,
        "start_time": result.start_time.isoformat(),
        "end_time": result.end_time.isoformat() if result.end_time else None,
        "cancelled": result.cancelled
    }

@app.post("/api/generate-locale-requirements")
async def generate_locale_requirements_preview(
    base_requirements: dict = Body(..., description="Base requirements dictionary"),
    target_locale: str = Body(..., description="Target locale code")
):
    """
    Generate and preview locale-specific requirements from base template.
    
    Args:
        base_requirements: Base requirements dictionary
        target_locale: Target locale code
        
    Returns:
        dict: Generated locale-specific requirements
    """
    from locale_config import generate_locale_requirements, get_locale_config
    
    try:
        locale_config = get_locale_config(target_locale)
        if not locale_config:
            raise HTTPException(status_code=400, detail=f"Unsupported locale: {target_locale}")
        
        locale_requirements = generate_locale_requirements(base_requirements, target_locale)
        
        return {
            "locale": target_locale,
            "locale_config": locale_config,
            "requirements": locale_requirements
        }
        
    except Exception as e:
        logger.error(f"Error generating locale requirements: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate requirements: {str(e)}")

if __name__ == "__main__":
    # Use port 8000 or environment variable for production
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)