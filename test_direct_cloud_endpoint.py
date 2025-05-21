"""
Direct testing endpoint for cloud browser detection.
A simple FastAPI endpoint to test the cloud detection directly, 
avoiding the complexity of the main application.
"""
import os
import logging
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional
from cloud_browser_automation import check_for_product_tables_cloud

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create the FastAPI application
app = FastAPI(title="Cloud Browser Detection Tester")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/test-cloud-detection")
async def test_cloud_detection(
    urls: List[str] = Body(..., description="List of URLs to check for product tables"),
    timeout: Optional[int] = Body(20, description="Timeout for product table checks in seconds")
):
    """
    Test the cloud browser detection for product tables.
    This endpoint directly uses the cloud_browser_automation module
    to test detection of product tables in React-rendered applications.
    
    Args:
        urls: List of URLs to check for product tables
        timeout: Timeout for each check in seconds (default: 20)
        
    Returns:
        dict: Results of product table detection for each URL
    """
    results = {}
    
    # Process each URL
    for url in urls:
        logger.info(f"Testing cloud detection for URL: {url} (timeout: {timeout}s)")
        
        try:
            # Call cloud browser detection function directly
            result = check_for_product_tables_cloud(url, timeout)
            results[url] = result
            logger.info(f"Result for {url}: {result}")
        except Exception as e:
            logger.error(f"Error processing {url}: {str(e)}")
            results[url] = {
                "found": None,
                "class_name": None,
                "detection_method": "error",
                "message": f"Error during detection: {str(e)}"
            }
    
    # Return the results
    return {"results": results}

@app.get("/")
async def get_root():
    """Root endpoint that displays basic usage information."""
    return {
        "info": "Cloud Browser Detection Test API",
        "usage": "POST to /test-cloud-detection with a list of URLs to test"
    }

# Run the FastAPI app if executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001)