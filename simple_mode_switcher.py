"""
Simple mode-switching implementation for the Email QA System.
"""

import os
import shutil
import tempfile
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from typing import Optional
from email_qa_enhanced import validate_email
from runtime_config import config

# Set up logging
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

@app.post("/run-qa")
async def run_qa(
    email: UploadFile = File(...), 
    requirements: UploadFile = File(...),
    force_production: Optional[bool] = Query(False, description="Force production mode for this request"),
    force_development: Optional[bool] = Query(False, description="Force development mode for this request")
):
    """
    Run QA validation on the uploaded email HTML against the provided requirements JSON.
    
    Args:
        email: HTML file of the email to validate
        requirements: JSON file containing validation requirements
        force_production: If True, temporarily run in production mode
        force_development: If True, temporarily run in development mode
    
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
        
        # Run validation
        results = validate_email(email_path, req_path)
        
        # Add force mode info to results
        if force_production:
            results["forced_mode"] = "production"
        elif force_development:
            results["forced_mode"] = "development"
        
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