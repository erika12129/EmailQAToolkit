import os
import shutil
import tempfile
from typing import Optional, Dict, Any
import base64
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from email_qa import validate_email, parse_email_html

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

# Global variable to store the last uploaded email for preview
last_uploaded_email = None
last_validation_results = None

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

@app.get("/preview")
async def preview_page():
    """Serve the interactive preview page."""
    from fastapi.responses import HTMLResponse
    with open("static/preview.html", "r") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/preview-email")
async def preview_email():
    """Serve the last uploaded email HTML for preview."""
    global last_uploaded_email
    
    if not last_uploaded_email:
        return JSONResponse(
            status_code=404,
            content={"detail": "No email has been uploaded yet for preview."}
        )
    
    return HTMLResponse(content=last_uploaded_email)

@app.get("/validation-results")
async def get_validation_results():
    """Get the latest validation results for the preview overlay."""
    global last_validation_results
    
    if not last_validation_results:
        return JSONResponse(
            status_code=404,
            content={"detail": "No validation results available yet."}
        )
    
    return JSONResponse(content=last_validation_results)

@app.post("/preview-upload")
async def preview_upload(email: UploadFile = File(...)):
    """
    Upload and store an email HTML file for preview without running full validation.
    """
    try:
        # Read the email file content
        contents = await email.read()
        email_content = contents.decode("utf-8")
        
        # Store for preview endpoint
        global last_uploaded_email
        last_uploaded_email = email_content
        
        # Return success
        return JSONResponse(
            content={"detail": "Email stored for preview successfully."}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing email HTML: {str(e)}")

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
        
        # Read email content before saving to file
        email_content = await email.read()
        
        # Store the email HTML for preview
        global last_uploaded_email
        last_uploaded_email = email_content.decode("utf-8")
        
        # Write the content to the file
        with open(email_path, "wb") as buffer:
            buffer.write(email_content)
        
        # Reset file position for the requirements file
        requirements.file.seek(0)
        
        with open(req_path, "wb") as buffer:
            shutil.copyfileobj(requirements.file, buffer)
        
        # Run validation
        results = validate_email(email_path, req_path)
        
        # Store validation results for preview overlay
        global last_validation_results
        last_validation_results = results
        
        return results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"QA validation failed: {str(e)}")
    
    finally:
        # Clean up temporary files
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    import uvicorn
    # Using port 5000 which is recommended for Replit
    uvicorn.run(app, host="0.0.0.0", port=5000)
