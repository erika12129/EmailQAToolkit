"""
Runtime configuration for Email QA that can be changed without restarting.
Provides mode switching between development and production.
"""

import os
import logging
import json

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Helper function to load secrets from Replit
def _load_api_keys_from_replit():
    """Load API keys from Replit secrets files."""
    try:
        # Check if we're in Replit environment
        is_replit = os.environ.get('REPL_ID') is not None or os.environ.get('REPLIT_ENVIRONMENT') is not None
        
        if is_replit:
            # Define paths for potential secret storage locations in Replit
            replit_secret_path = "/tmp/secrets.json"
            alt_secret_path = os.path.expanduser("~/.config/secrets.json")
            
            # Try to load from potential secret locations
            secret_locations = [replit_secret_path, alt_secret_path]
            for secret_file in secret_locations:
                if os.path.exists(secret_file):
                    try:
                        with open(secret_file, "r") as f:
                            secrets = json.load(f)
                            # Check for API keys in the loaded secrets
                            if "SCRAPINGBEE_API_KEY" in secrets and not os.environ.get("SCRAPINGBEE_API_KEY"):
                                os.environ["SCRAPINGBEE_API_KEY"] = secrets["SCRAPINGBEE_API_KEY"]
                                logger.info(f"Loaded ScrapingBee API key from {secret_file}")
                            
                            if "BROWSERLESS_API_KEY" in secrets and not os.environ.get("BROWSERLESS_API_KEY"):
                                os.environ["BROWSERLESS_API_KEY"] = secrets["BROWSERLESS_API_KEY"]
                                logger.info(f"Loaded Browserless API key from {secret_file}")
                                
                            return True
                    except Exception as e:
                        logger.error(f"Error loading secrets from {secret_file}: {str(e)}")
    except Exception as e:
        logger.error(f"Error loading API keys from Replit secrets: {str(e)}")
    
    return False

# Try to load secrets at module import time
_load_api_keys_from_replit()

class RuntimeConfig:
    """Runtime configuration that can be changed without restarting."""
    
    def __init__(self):
        # Check if this is a deployment environment
        self.is_deployment_env = os.environ.get("REPL_SLUG") is not None and os.environ.get("REPL_OWNER") is not None
        
        # Default to production mode for stability
        self.mode = os.environ.get("EMAIL_QA_MODE", "production")
        
        # Force development mode in preview environments
        if not self.is_deployment_env and os.environ.get("EMAIL_QA_FORCE_PROD") != "1":
            self.mode = "development"
            logger.info("Preview environment detected, forcing development mode")
            
        # Set default values (will be overridden by _update_settings_for_mode)
        self.enable_test_redirects = True
        self.product_table_timeout = 10
        
        # Check browser automation availability
        self.browser_automation_available = False
        
        # Check if we're in a Replit environment
        is_replit = os.environ.get('REPL_ID') is not None or os.environ.get('REPLIT_ENVIRONMENT') is not None
        
        # Check if this is a deployed app (not just a Replit dev environment)
        is_deployed = os.environ.get('REPLIT_ENVIRONMENT') == 'production'
        
        # Check for cloud browser API keys first (works in any environment)
        self.cloud_browser_available = False
        try:
            # Check for cloud browser API keys
            scrapingbee_key = os.environ.get('SCRAPINGBEE_API_KEY', '')
            browserless_key = os.environ.get('BROWSERLESS_API_KEY', '')
            self.cloud_browser_available = bool(scrapingbee_key or browserless_key)
            
            # Store the API keys for re-checking
            self.scrapingbee_key = scrapingbee_key
            self.browserless_key = browserless_key
            
            if self.cloud_browser_available:
                key_preview = scrapingbee_key[:4] + "..." if scrapingbee_key else browserless_key[:4] + "..."
                logger.info(f"Cloud browser API key found ({key_preview}) - cloud browser automation is available")
            else:
                logger.info("No cloud browser API keys found")
            
            # Try to re-check local browser too, if possible
            local_available = False
            try:
                from browser_detection import run_full_detection
                local_available = run_full_detection()
            except Exception as e:
                logger.error(f"Error checking local browser availability: {str(e)}")
                local_available = False
            
            # Update overall status
            old_status = self.browser_automation_available
            self.browser_automation_available = self.cloud_browser_available or local_available
            logger.info(f"Updated browser automation status: {self.browser_automation_available} (Cloud: {self.cloud_browser_available}, Local: {local_available})")
        
        except Exception as e:
            logger.error(f"Error in browser automation detection: {str(e)}")
            self.browser_automation_available = False
        
        finally:
            # Always update settings for the current mode, regardless of errors
            self._update_settings_for_mode()
    
    def _update_settings_for_mode(self):
        """Update settings based on current mode."""
        if self.mode == "development":
            self.enable_test_redirects = True
            self.product_table_timeout = 30  # Longer timeout in development
            self.request_timeout = 10
            self.max_retries = 2
            self.test_domains = {"localhost:5001"}
            logger.info("Using DEVELOPMENT configuration")
        else:  # Production mode
            self.enable_test_redirects = False  # Never redirect to test in production
            self.product_table_timeout = 20  # Shorter timeout for production
            self.request_timeout = 8
            self.max_retries = 3
            self.test_domains = set()  # No test domains in production
            logger.info("Using PRODUCTION configuration")
    
    def is_development(self):
        """Check if running in development mode."""
        return self.mode == "development"
    
    def is_production(self):
        """Check if running in production mode."""
        return self.mode == "production"
    
    def refresh_browser_automation_status(self):
        """Refresh the browser automation status without restarting the application."""
        # Try to load API keys from Replit secrets first
        _load_api_keys_from_replit()
        
        # Store old status to check if it changed
        old_status = self.browser_automation_available
        old_cloud = self.cloud_browser_available
        
        # Re-check cloud API keys (in case they were added/removed)
        scrapingbee_key = os.environ.get('SCRAPINGBEE_API_KEY', '')
        browserless_key = os.environ.get('BROWSERLESS_API_KEY', '')
        
        # Update cloud status
        self.cloud_browser_available = bool(scrapingbee_key or browserless_key)
        
        # Check if keys changed
        keys_changed = (scrapingbee_key != getattr(self, 'scrapingbee_key', '') or 
                       browserless_key != getattr(self, 'browserless_key', ''))
        
        # Update stored keys
        self.scrapingbee_key = scrapingbee_key
        self.browserless_key = browserless_key
        
        # Only log if status changed
        if self.cloud_browser_available != old_cloud:
            if self.cloud_browser_available:
                key_preview = scrapingbee_key[:4] + "..." if scrapingbee_key else browserless_key[:4] + "..."
                logger.info(f"Cloud browser API key status changed: Now available ({key_preview})")
            else:
                logger.info("Cloud browser API key status changed: Now unavailable")
        elif keys_changed and self.cloud_browser_available:
            # If keys changed but availability remained, still log the change
            key_preview = scrapingbee_key[:4] + "..." if scrapingbee_key else browserless_key[:4] + "..."
            logger.info(f"Cloud browser API key changed: Now using {key_preview}")
        
        # Try to re-check local browser too, if possible
        local_available = False
        try:
            from browser_detection import run_full_detection
            local_available = run_full_detection()
        except Exception as e:
            logger.error(f"Error checking local browser availability: {str(e)}")
            local_available = False
        
        # Update overall status
        self.browser_automation_available = self.cloud_browser_available or local_available
        
        # Log changes
        if self.browser_automation_available != old_status:
            logger.info(f"Browser automation status changed: {old_status} -> {self.browser_automation_available}")
            logger.info(f"Current status - Cloud: {self.cloud_browser_available}, Local: {local_available}")
        
        # Return True if status changed, False otherwise
        return self.browser_automation_available != old_status
    
    def set_mode(self, mode):
        """
        Set the runtime mode.
        
        Args:
            mode: 'development' or 'production'
        """
        if mode not in ["development", "production"]:
            logger.error(f"Invalid mode: {mode}, must be 'development' or 'production'")
            return False
        
        old_mode = self.mode
        self.mode = mode
        self._update_settings_for_mode()
        
        # Log mode change
        logger.info(f"Mode changed: {old_mode} -> {self.mode}")
        return True
    
    def create_test_url(self, url):
        """
        Create a test URL for the given production URL.
        
        Args:
            url: The original URL
            
        Returns:
            str: The test URL
        """
        from urllib.parse import urlparse, parse_qs
        
        url_parts = urlparse(url)
        domain = url_parts.netloc
        
        # Extract language info from domain or path
        if '/es-mx' in url_parts.path or '.mx.' in domain or domain.endswith('.mx'):
            lang = 'es-mx'
        else:
            lang = 'en'
        
        # Create local test URL
        path = url_parts.path if url_parts.path and url_parts.path != '/' else f"/{lang}"
        if not path.startswith('/'):
            path = f"/{path}"
        
        test_url = f"http://localhost:5001{path}"
        
        # Forward query parameters
        if url_parts.query:
            test_url += f"?{url_parts.query}"
            
        return test_url
            
# Create a global instance
config = RuntimeConfig()