"""
Main FastAPI application for Email QA Automation with production support.
"""

import os
import shutil
import tempfile
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse, FileResponse
from pydantic import BaseModel
from typing import Optional

# Import the production-ready email_qa module
from email_qa_prod import validate_email
from config import config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Email QA Automation API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Mount attached assets
app.mount("/attached_assets", StaticFiles(directory="attached_assets"), name="attached_assets")

# Environment indicator for UI
env_status = "PRODUCTION" if config.is_production else "DEVELOPMENT"
logger.info(f"Running in {env_status} environment")

@app.get("/")
async def read_root():
    """Serve the frontend application directly."""
    with open("static/index.html", "r") as f:
        html_content = f.read()
        
    # Add environment indicator to HTML
    env_indicator = f"""
    <div style="position: fixed; bottom: 10px; left: 10px; background-color: {
        '#f56565' if config.is_production else '#4299e1'
    }; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px; z-index: 1000;">
        {env_status}
    </div>
    """
    
    # Insert the indicator before the closing body tag
    html_content = html_content.replace("</body>", f"{env_indicator}</body>")
    
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/test")
async def test_page():
    """Serve a simple test page directly."""
    with open("static/simple.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/config")
async def get_config():
    """Return the current configuration settings (safe fields only)."""
    # Only return non-sensitive configuration items
    safe_config = {
        "environment": "production" if config.is_production else "development",
        "enable_test_redirects": config.enable_test_redirects,
        "max_retries": config.max_retries,
        "request_timeout": config.request_timeout,
        "default_language": config.default_language,
        "version": config.config_data.get("version", "1.0.0")
    }
    return JSONResponse(content=safe_config)

@app.get("/domains")
async def get_domains():
    """Return a list of configured domains."""
    domains = {
        "primary": list(config.primary_domains.keys()),
        "test": list(config.test_domains.keys())
    }
    return JSONResponse(content=domains)

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
            <title>UTM Campaign Validation Guide</title>
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

@app.post("/run-qa", response_class=JSONResponse)
async def run_qa(
    email: UploadFile = File(...), 
    requirements: UploadFile = File(...),
    force_production: Optional[bool] = Query(True, description="Force production mode for this request")
):
    """
    Run QA validation on the uploaded email HTML against the provided requirements JSON.
    
    Args:
        email: HTML file of the email to validate
        requirements: JSON file containing validation requirements
        force_production: If True, disables test redirects for this request only, default is True
    
    Returns:
        dict: Validation results
    """
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    
    # If force_production is true, temporarily modify the environment
    original_environment = None
    
    if force_production:
        logger.info("Forcing production mode for this request")
        # To enable production mode, we just need to change the environment
        # The is_production and enable_test_redirects properties will automatically update
        original_environment = config.environment
        config.environment = "production"
        
        # Log the changes
        logger.info(f"Temporarily switched to production mode:")
        logger.info(f"  - environment: {config.environment}")
        logger.info(f"  - is_production: {config.is_production}")
        logger.info(f"  - enable_test_redirects: {config.enable_test_redirects}")
    
    try:
        # Save uploaded files
        email_path = os.path.join(temp_dir, "email.html")
        req_path = os.path.join(temp_dir, "requirements.json")
        
        with open(email_path, "wb") as buffer:
            shutil.copyfileobj(email.file, buffer)
        
        with open(req_path, "wb") as buffer:
            shutil.copyfileobj(requirements.file, buffer)
        
        # Run validation
        results = validate_email(email_path, req_path)
        
        # Add environment information to results
        results["environment"] = "production" if config.is_production or force_production else "development"
        results["force_production"] = force_production
        
        # Explicitly return as JSON with appropriate headers
        return JSONResponse(
            content=results,
            media_type="application/json"
        )
    
    except Exception as e:
        error_detail = f"QA validation failed: {str(e)}"
        logger.error(error_detail)
        return JSONResponse(
            status_code=500,
            content={"detail": error_detail},
            media_type="application/json"
        )
    
    finally:
        # Restore original environment if modified
        if force_production and original_environment is not None:
            config.environment = original_environment
            
            logger.info(f"Restored original environment settings:")
            logger.info(f"  - environment: {config.environment}")
            logger.info(f"  - is_production: {config.is_production}")
            logger.info(f"  - enable_test_redirects: {config.enable_test_redirects}")
        
        # Clean up temporary files
        shutil.rmtree(temp_dir)

@app.get("/reload-config")
async def reload_configuration():
    """Reload the configuration from disk."""
    try:
        config.reload_config()
        return JSONResponse(content={"status": "success", "message": "Configuration reloaded successfully"})
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": f"Failed to reload configuration: {str(e)}"}
        )

if __name__ == "__main__":
    import uvicorn
    import os
    # Use port 8000 for production, 5000 for development
    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)