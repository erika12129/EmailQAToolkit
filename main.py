import os
import shutil
import tempfile
from typing import List
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
    expose_headers=["*"]
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/assets", StaticFiles(directory="attached_assets"), name="assets")

@app.get("/")
async def read_root():
    """Serve the frontend application directly."""
    from fastapi.responses import HTMLResponse
    try:
        with open("index.html", "r") as f:
            html_content = f.read()
    except FileNotFoundError:
        try:
            with open("attached_assets/index.html", "r") as f:
                html_content = f.read()
        except FileNotFoundError:
            # Fallback to static/index.html if other files are not found
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

@app.post("/run-localized-qa")
async def run_localized_qa(
    localized_email: UploadFile = File(...), 
    localized_requirements: UploadFile = File(...),
    parent_email: UploadFile = None,
    parent_requirements: UploadFile = None,
    compare_to_parent: bool = False
):
    """
    Run QA validation on localized email with optional comparison to parent (en_US) version.
    
    Args:
        localized_email: HTML file of the localized email to validate
        localized_requirements: JSON file containing localized validation requirements
        parent_email: HTML file of the parent (en_US) email (optional)
        parent_requirements: JSON file containing parent validation requirements (optional)
        compare_to_parent: Whether to compare the localized email to the parent email
        
    Returns:
        dict: Combined validation results
    """
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Save localized files
        localized_email_path = os.path.join(temp_dir, "localized_email.html")
        localized_req_path = os.path.join(temp_dir, "localized_requirements.json")
        
        with open(localized_email_path, "wb") as buffer:
            shutil.copyfileobj(localized_email.file, buffer)
        
        with open(localized_req_path, "wb") as buffer:
            shutil.copyfileobj(localized_requirements.file, buffer)
        
        # If comparing to parent, save parent files
        parent_email_path = None
        parent_req_path = None
        
        if compare_to_parent and parent_email and parent_requirements:
            parent_email_path = os.path.join(temp_dir, "parent_email.html")
            parent_req_path = os.path.join(temp_dir, "parent_requirements.json")
            
            with open(parent_email_path, "wb") as buffer:
                shutil.copyfileobj(parent_email.file, buffer)
            
            with open(parent_req_path, "wb") as buffer:
                shutil.copyfileobj(parent_requirements.file, buffer)
        
        # Run validation with localized requirements
        results = validate_email(
            localized_email_path, 
            localized_req_path,
            compare_to_parent=compare_to_parent,
            parent_email_path=parent_email_path
        )
        
        # If comparing to parent, also validate against parent requirements
        if compare_to_parent and parent_email_path and parent_req_path:
            parent_req_results = validate_email(
                localized_email_path,
                parent_req_path,
                compare_to_parent=False
            )
            
            results['parent_requirements_validation'] = {
                'metadata': parent_req_results['metadata'],
                'links': parent_req_results['links']
            }
        
        return results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Localized QA validation failed: {str(e)}")
    
    finally:
        # Clean up temporary files
        shutil.rmtree(temp_dir)

@app.post("/run-batch-qa")
async def run_batch_qa(
    emails: List[UploadFile] = File(...),
    requirements: UploadFile = File(...)
):
    """
    Run QA validation on multiple email HTML files against the same requirements.
    
    Args:
        emails: List of HTML files to validate
        requirements: JSON file containing validation requirements
        
    Returns:
        dict: Mapping of email filenames to validation results
    """
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Save requirements file
        req_path = os.path.join(temp_dir, "requirements.json")
        with open(req_path, "wb") as buffer:
            shutil.copyfileobj(requirements.file, buffer)
        
        # Process each email file
        batch_results = {}
        for email_file in emails:
            email_path = os.path.join(temp_dir, email_file.filename)
            
            with open(email_path, "wb") as buffer:
                shutil.copyfileobj(email_file.file, buffer)
            
            # Run validation and store results by filename
            results = validate_email(email_path, req_path)
            batch_results[email_file.filename] = results
        
        return batch_results
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch QA validation failed: {str(e)}")
    
    finally:
        # Clean up temporary files
        shutil.rmtree(temp_dir)

if __name__ == "__main__":
    import uvicorn
    # Using port 5000 which is recommended for Replit
    uvicorn.run(app, host="0.0.0.0", port=5000)
