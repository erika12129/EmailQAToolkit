#!/usr/bin/env python3
"""
Production deployment entry point for Email QA System.
Optimized for Cloud Run with proper port configuration and error handling.
"""

import os
import sys
import logging
import uvicorn

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Main deployment entry point with comprehensive error handling."""
    
    # Set production environment variables
    os.environ.setdefault("DEPLOYMENT_MODE", "production")
    os.environ.setdefault("SKIP_BROWSER_CHECK", "true")
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    
    # Cloud Run expects port 8000 (configured in .replit)
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    
    # Log deployment configuration
    logger.info("=" * 60)
    logger.info("Email QA System - Production Deployment")
    logger.info("=" * 60)
    logger.info(f"Host: {host}")
    logger.info(f"Port: {port}")
    logger.info(f"Deployment Mode: {os.environ.get('DEPLOYMENT_MODE', 'development')}")
    logger.info(f"Skip Browser Check: {os.environ.get('SKIP_BROWSER_CHECK', 'false')}")
    logger.info(f"Python Unbuffered: {os.environ.get('PYTHONUNBUFFERED', 'false')}")
    logger.info("=" * 60)
    
    try:
        # Import the FastAPI app
        logger.info("Loading FastAPI application...")
        from simple_mode_switcher import app
        logger.info("FastAPI application loaded successfully")
        
        # Configure uvicorn settings for production (simplified for compatibility)
        uvicorn_config = {
            "app": app,
            "host": host,
            "port": port,
            "log_level": "info",
            "access_log": True,
            "lifespan": "on"
        }
        
        logger.info("Starting uvicorn server with production configuration...")
        uvicorn.run(**uvicorn_config)
        
    except ImportError as e:
        logger.error(f"Failed to import FastAPI application: {e}")
        logger.error("This indicates a missing dependency or import error")
        sys.exit(1)
        
    except OSError as e:
        if "Address already in use" in str(e):
            logger.error(f"Port {port} is already in use")
            logger.error("Try setting a different PORT environment variable")
        else:
            logger.error(f"Network error: {e}")
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"Unexpected error during startup: {e}")
        logger.error("Check the application logs for more details")
        sys.exit(1)

if __name__ == "__main__":
    main()