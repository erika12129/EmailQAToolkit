"""
API endpoints for the Email QA System.
Contains cloud browser API configuration endpoints.
"""

import os
import logging
import json
from fastapi import APIRouter, Body, HTTPException
from fastapi.responses import JSONResponse
from typing import Optional, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)

# Create an APIRouter instance
router = APIRouter()

# Check if cloud API test module is available
try:
    import cloud_api_test
    CLOUD_API_TEST_AVAILABLE = True
    logger.info("Cloud API test module loaded successfully")
except ImportError:
    CLOUD_API_TEST_AVAILABLE = False
    logger.warning("Cloud API test module not available")

@router.get("/cloud-browser-status")
async def get_cloud_browser_status():
    """Get the status of cloud browser APIs."""
    try:
        if CLOUD_API_TEST_AVAILABLE:
            from cloud_api_test import get_api_status
            
            # Get the API status with additional safeguards
            try:
                status = get_api_status()
                
                # Validate the structure of the status response
                if not isinstance(status, dict):
                    logger.error(f"Invalid status response: {status}")
                    raise ValueError("Invalid status response format")
                
                # Ensure the expected keys exist
                if "cloud_browser_available" not in status:
                    status["cloud_browser_available"] = False
                
                # Add headers to ensure proper content type
                return JSONResponse(
                    content=status,
                    headers={"Content-Type": "application/json"}
                )
            except Exception as inner_e:
                logger.error(f"Error processing API status: {str(inner_e)}")
                return JSONResponse(
                    status_code=500,
                    content={
                        "cloud_browser_available": False,
                        "error": f"Error processing API status: {str(inner_e)}"
                    },
                    headers={"Content-Type": "application/json"}
                )
        else:
            return JSONResponse(
                content={
                    "cloud_browser_available": False,
                    "error": "Cloud browser API module not available"
                },
                headers={"Content-Type": "application/json"}
            )
    except Exception as e:
        logger.error(f"Error getting cloud browser status: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "cloud_browser_available": False,
                "error": f"Failed to get cloud browser status: {str(e)}"
            },
            headers={"Content-Type": "application/json"}
        )

@router.post("/set-cloud-api-key")
async def set_cloud_api_key(
    api_key: str = Body(..., description="The API key to set"),
    service: str = Body(..., description="The service to set the API key for ('scrapingbee' or 'browserless')")
):
    """Set a cloud browser API key."""
    try:
        # Validate service name
        if service not in ['scrapingbee', 'browserless']:
            return JSONResponse(
                status_code=400,
                content={"error": f"Invalid service: {service}. Must be 'scrapingbee' or 'browserless'"}
            )
        
        # Set the API key as an environment variable
        env_var = "SCRAPINGBEE_API_KEY" if service == "scrapingbee" else "BROWSERLESS_API_KEY"
        os.environ[env_var] = api_key
        
        # Add some debug logging
        logger.info(f"Setting {env_var} environment variable to new value: {api_key[:4]}...")
        
        # Import cloud browser automation to update its global variables
        try:
            import cloud_browser_automation
            if service == "scrapingbee":
                cloud_browser_automation.SCRAPINGBEE_API_KEY = api_key
            else:
                cloud_browser_automation.BROWSERLESS_API_KEY = api_key
            logger.info(f"Updated cloud_browser_automation.{service.upper()}_API_KEY variable directly")
        except ImportError:
            logger.warning("Could not import cloud_browser_automation module to update API key")
            
        # Update runtime configuration to reflect the new browser automation status
        try:
            from runtime_config import config
            status_changed = config.refresh_browser_automation_status()
            logger.info(f"Refreshed browser automation status, changed: {status_changed}")
        except Exception as e:
            logger.error(f"Error refreshing browser automation status: {str(e)}")
        
        # Test the API key if possible
        if CLOUD_API_TEST_AVAILABLE:
            from cloud_api_test import test_cloud_api
            test_result = test_cloud_api(api_key, service)
            
            # If test was successful, return success message
            if test_result.get('success', False):
                return JSONResponse(content={
                    "success": True,
                    "message": f"{service} API key set and tested successfully",
                    "test_result": test_result
                })
            else:
                # Key was set but test failed
                return JSONResponse(
                    status_code=400,
                    content={
                        "success": False,
                        "message": f"{service} API key was set but test failed",
                        "test_result": test_result
                    }
                )
        else:
            # No test module available
            return JSONResponse(content={
                "success": True,
                "message": f"{service} API key set (untested)",
                "warning": "Cloud API test module not available to verify key"
            })
    except Exception as e:
        logger.error(f"Error setting cloud API key: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to set cloud API key: {str(e)}"}
        )

@router.post("/test-cloud-api")
async def test_cloud_api_endpoint(
    api_key: Optional[str] = Body(None, description="The API key to test (will use stored key if not provided)"),
    service: Optional[str] = Body(None, description="The service to test ('scrapingbee' or 'browserless', will test both if not specified)")
):
    """Test a cloud browser API key."""
    try:
        if CLOUD_API_TEST_AVAILABLE:
            from cloud_api_test import test_cloud_api
            test_result = test_cloud_api(api_key, service)
            return JSONResponse(content=test_result)
        else:
            return JSONResponse(
                status_code=400,
                content={"error": "Cloud API test module not available"}
            )
    except Exception as e:
        logger.error(f"Error testing cloud API key: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to test cloud API key: {str(e)}"}
        )