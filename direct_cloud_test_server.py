"""
Direct Cloud Detection Test Server

A simple standalone server to test the cloud browser detection functionality.
This avoids all the complexity in the main application.
"""
import os
import uvicorn
import logging
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from cloud_browser_automation import check_for_product_tables_cloud

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create the FastAPI application
app = FastAPI(title="Direct Cloud Detection Tester")

# Create templates directory if it doesn't exist
os.makedirs("templates", exist_ok=True)

# Create a simple HTML template for the form
with open("templates/cloud_test.html", "w") as f:
    f.write("""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Cloud Detection Test</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            h1 {
                color: #333;
            }
            .input-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
            }
            input[type="text"], input[type="number"] {
                width: 100%;
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
            }
            button {
                background-color: #4CAF50;
                color: white;
                padding: 10px 15px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
            }
            button:hover {
                background-color: #45a049;
            }
            pre {
                margin-top: 20px;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #f9f9f9;
                white-space: pre-wrap;
                max-height: 400px;
                overflow-y: auto;
            }
            .success {
                color: green;
                font-weight: bold;
            }
            .error {
                color: red;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <h1>Direct Cloud Detection Test</h1>
        <form action="/test" method="post">
            <div class="input-group">
                <label for="url">URL to Test:</label>
                <input type="text" id="url" name="url" value="https://partly-products-showcase.lovable.app/products" required>
            </div>
            <div class="input-group">
                <label for="timeout">Timeout (seconds):</label>
                <input type="number" id="timeout" name="timeout" value="20" min="1" max="60">
            </div>
            <button type="submit">Run Test</button>
        </form>
        
        {% if result %}
        <h2>Test Results</h2>
        <p>
            <strong>Product Table Found:</strong> 
            {% if result.found %}
            <span class="success">YES</span>
            {% elif result.found is none %}
            <span class="error">UNKNOWN</span>
            {% else %}
            <span class="error">NO</span>
            {% endif %}
        </p>
        <p><strong>Class Name:</strong> {{ result.class_name or "None" }}</p>
        <p><strong>Detection Method:</strong> {{ result.detection_method or "None" }}</p>
        <p><strong>Message:</strong> {{ result.message or "None" }}</p>
        
        <h3>Raw Response</h3>
        <pre>{{ raw_result }}</pre>
        {% endif %}
    </body>
    </html>
    """)

# Set up templates
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request):
    """Serve the form for testing cloud detection."""
    return templates.TemplateResponse("cloud_test.html", {"request": request})

@app.post("/test", response_class=HTMLResponse)
async def run_test(request: Request, url: str = Form(...), timeout: int = Form(20)):
    """Run the cloud detection test and display results."""
    logger.info(f"Testing URL: {url} with timeout: {timeout}s")
    
    try:
        # Call cloud detection directly
        result = check_for_product_tables_cloud(url, timeout)
        logger.info(f"Test result: {result}")
        
        # Format the raw result for display
        import json
        raw_result = json.dumps(result, indent=2)
        
        return templates.TemplateResponse(
            "cloud_test.html", 
            {
                "request": request, 
                "result": result, 
                "raw_result": raw_result
            }
        )
    except Exception as e:
        logger.error(f"Error testing URL {url}: {str(e)}")
        error_result = {
            "found": None,
            "class_name": None,
            "detection_method": "error",
            "message": f"Error: {str(e)}"
        }
        return templates.TemplateResponse(
            "cloud_test.html", 
            {
                "request": request, 
                "result": error_result, 
                "raw_result": str(e)
            }
        )

if __name__ == "__main__":
    logger.info("Starting Direct Cloud Detection Test Server on port 5001")
    uvicorn.run(app, host="0.0.0.0", port=5001)