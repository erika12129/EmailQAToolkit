import uvicorn
import os
import signal
import sys
import logging
from runtime_config import config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import browser detection
try:
    import browser_detection
    logger.info("Browser detection module loaded")
except ImportError:
    logger.warning("Browser detection module not available")

def run_server():
    """
    Start only the FastAPI server for production deployment.
    This is a simplified version of run_servers.py that:
    1. Sets production mode
    2. Only starts the main FastAPI application (no test website)
    3. Optimized for deployment environments
    4. Automatically detects available browsers
    """
    # Explicitly set production mode
    config.set_mode("production")
    logger.info("Starting Email QA Automation in PRODUCTION mode for deployment...")
    
    # Set environment variable for configuration
    os.environ["EMAIL_QA_MODE"] = "production"
    
    # Run browser detection if available
    browser_available = False
    try:
        if 'browser_detection' in sys.modules:
            logger.info("Running browser detection...")
            browser_available = browser_detection.run_full_detection()
            if browser_available:
                logger.info("Browser automation is available and configured")
            else:
                logger.warning("No compatible browsers detected - will use HTTP fallback methods")
    except Exception as e:
        logger.error(f"Error during browser detection: {e}")
        logger.warning("Browser detection failed - will use HTTP fallback methods")
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        print("\nShutting down server...")
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Import the FastAPI app - import here to ensure config is set correctly
    from simple_mode_switcher import app
    
    # Start the server
    print("Starting FastAPI server on port 5000")
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")

if __name__ == "__main__":
    run_server()