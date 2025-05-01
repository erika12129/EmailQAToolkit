"""
Enhanced FastAPI application for Email QA Automation with mode switching.
"""

import os
import shutil
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from typing import Optional
from email_qa_enhanced import validate_email
from runtime_config import config
import logging

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

@app.get("/")
async def read_root():
    """Serve the frontend application with mode indicator."""
    with open("static/index.html", "r") as f:
        html_content = f.read()
        
    # Add mode indicator to the UI
    prod_color = '#e53e3e'
    dev_color = '#3182ce'
    current_color = prod_color if config.is_production else dev_color
    new_mode = 'production' if config.is_development else 'development'
    
    mode_indicator = f"""
    <div style="position: fixed; bottom: 10px; right: 10px; 
         background-color: {current_color}; 
         color: white; padding: 6px 12px; border-radius: 4px; 
         font-size: 12px; font-weight: bold; z-index: 1000; 
         display: flex; align-items: center; gap: 6px;">
        <span>Mode: {config.mode.upper()}</span>
        <button id="toggle-mode-btn" 
                style="background-color: white; color: {current_color}; 
                border: none; border-radius: 3px; padding: 2px 8px; 
                font-size: 11px; cursor: pointer; font-weight: bold;"
                data-new-mode="{new_mode}">
            Switch
        </button>
    </div>
    
    <script>
        // Add mode switching functionality
        document.addEventListener('DOMContentLoaded', function() {
            var toggleBtn = document.getElementById('toggle-mode-btn');
            if (toggleBtn) {
                toggleBtn.addEventListener('click', function() {
                    var newMode = toggleBtn.getAttribute('data-new-mode');
                    fetch('/set-mode/' + newMode)
                        .then(response => response.json())
                        .then(data => {
                            console.log('Mode switched:', data);
                            window.location.reload();
                        })
                        .catch(error => {
                            console.error('Error switching mode:', error);
                            alert('Failed to switch mode: ' + error);
                        });
                });
            }
        });
    </script>
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
        result = config.set_mode(mode)
        return JSONResponse(content=result)
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"error": str(e)}
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to set mode: {str(e)}"}
        )

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
        # Restore original mode if it was changed
        if force_production or force_development:
            config.set_mode(original_mode)
        
        # Clean up temporary files
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    import uvicorn
    import os
    # Use port 8000 for production, 5000 for development
    port = int(os.environ.get("PORT", "5000"))
    uvicorn.run(app, host="0.0.0.0", port=port)