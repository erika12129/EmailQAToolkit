"""
Main entry point for the Email QA System application.
Used for both development and deployment.
"""
import os
import uvicorn
from runtime_config import config
from simple_mode_switcher import app as api_app

def main():
    """
    Start the Email QA System application.
    
    In deployment, only the FastAPI app is started.
    The test website server is not needed in production deployment.
    """
    # Set environment variable for configuration
    os.environ["EMAIL_QA_MODE"] = config.mode
    
    # Determine if this is a deployment environment
    is_deployment = os.environ.get("REPL_SLUG") is not None and os.environ.get("REPL_OWNER") is not None
    
    print(f"Starting Email QA System in {config.mode.upper()} mode...")
    print(f"Running in {'DEPLOYMENT' if is_deployment else 'LOCAL'} mode")
    
    # Start the FastAPI server
    uvicorn.run(api_app, host="0.0.0.0", port=5000)

if __name__ == "__main__":
    # For local development, run both servers using run_servers.py
    # For deployment, just run the FastAPI app
    main()