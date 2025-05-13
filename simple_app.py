"""
Simple web server for Email QA System with improved accessibility.
Serves static files for the UI and handles basic routing.
"""
import os
import logging
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import runtime configuration
from runtime_config import RuntimeConfig

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

@app.get("/config")
async def get_config():
    """Get current configuration settings for frontend."""
    runtime_config = RuntimeConfig()
    mode = runtime_config.mode if hasattr(runtime_config, "mode") else "production"
    logger.info(f"Serving config endpoint, mode={mode}")
    
    return JSONResponse(content={
        "mode": mode,
        "enable_test_redirects": False,
        "request_timeout": 10,
        "max_retries": 3,
        "test_domains": []
    })

@app.get("/")
async def read_root():
    """Serve the frontend application."""
    # Get runtime config instance
    runtime_config = RuntimeConfig()
    
    # Determine current mode
    is_prod_mode = runtime_config.is_production() if hasattr(runtime_config, "is_production") and callable(runtime_config.is_production) else True
    mode = "production" if is_prod_mode else "development"
    
    try:
        # Load HTML content
        with open("static/index.html", "r") as f:
            html_content = f.read()
        
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
    except Exception as e:
        logger.error(f"Error serving frontend: {str(e)}")
        return HTMLResponse(content=f"<html><body><h1>Error</h1><p>{str(e)}</p></body></html>", status_code=500)

@app.get("/set-mode/{mode}")
async def set_mode(mode: str):
    """Switch between development and production modes."""
    # Get runtime config instance
    runtime_config = RuntimeConfig()
    
    if mode not in ["development", "production"]:
        raise HTTPException(status_code=400, detail="Invalid mode. Must be 'development' or 'production'")
    
    # Set the mode
    if hasattr(runtime_config, "set_mode") and callable(runtime_config.set_mode):
        runtime_config.set_mode(mode)
    
    # Return success
    return JSONResponse(content={"success": True, "mode": mode})

@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy"}

# Add the missing API endpoints necessary for the frontend
@app.post("/run-qa")
async def run_qa(request: Request):
    """Simplified version for demo purposes."""
    return JSONResponse(content={
        "success": True,
        "status": "Demo mode - No actual validation performed",
        "metadata": {
            "sender": "demo@example.com",
            "subject": "Demo Email Subject",
            "preheader": "This is a demo preheader"
        },
        "images": [],
        "links": [
            {
                "text": "Example Link",
                "url": "https://example.com",
                "status": 200,
                "utm_params": {},
                "product_table_status": "Not checked",
                "product_table_class": None,
                "utm_issues": []
            }
        ]
    })

@app.post("/check-product-tables")
async def check_product_tables(request: Request):
    """Simplified version for demo purposes."""
    # Parse the request body
    try:
        body = await request.json()
        urls = body.get("urls", [])
    except:
        urls = []
    
    results = {}
    for url in urls:
        results[url] = {
            "found": True,
            "class_name": "demo-product-class",
            "detection_method": "demo",
            "bot_blocked": False
        }
    
    return JSONResponse(content=results)

# For standalone execution
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)