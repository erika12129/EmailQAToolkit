import os
import shutil
import tempfile
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from email_qa import validate_email

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
    """Serve the frontend application directly."""
    from fastapi.responses import HTMLResponse
    with open("static/index.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/test")
async def test_page():
    """Serve a simple test page directly."""
    from fastapi.responses import HTMLResponse
    with open("static/simple.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/attached_assets/{file_path:path}")
async def serve_asset(file_path: str):
    """Serve attached assets with proper content type."""
    from fastapi.responses import HTMLResponse, PlainTextResponse, FileResponse
    
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

@app.post("/run-qa")
async def run_qa(email: UploadFile = File(...), requirements: UploadFile = File(...)):
    """
    Run QA validation on the uploaded email HTML against the provided requirements JSON.
    
    Args:
        email: HTML file of the email to validate
        requirements: JSON file containing validation requirements
    
    Returns:
        dict: Validation results
    """
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
        
        # Run validation
        results = validate_email(email_path, req_path)
        return results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QA validation failed: {str(e)}")
    
    finally:
        # Clean up temporary files
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    import uvicorn
    # Using port 8000 for Autoscale deployment health checks
    uvicorn.run(app, host="0.0.0.0", port=8000)
