"""
Runtime configuration for Email QA that can be changed without restarting.
Provides mode switching between development and production.
"""

import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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
        
        # In Replit dev environment, browser automation is never available
        # But in deployed Replit app, it should be available
        if is_replit and not is_deployed:
            logger.info("Replit development environment detected - browser automation is unavailable")
            self.browser_automation_available = False
        elif is_replit and is_deployed:
            logger.info("Replit deployment environment detected - checking for browser automation")
            try:
                from selenium_automation import check_browser_availability
                self.browser_automation_available = check_browser_availability()
                logger.info(f"Browser automation available in deployment: {self.browser_automation_available}")
            except Exception as e:
                logger.error(f"Error checking browser automation availability in deployment: {str(e)}")
                self.browser_automation_available = False
        else:
            # Not in Replit at all
            try:
                from selenium_automation import check_browser_availability
                self.browser_automation_available = check_browser_availability()
                logger.info(f"Browser automation available: {self.browser_automation_available}")
            except Exception as e:
                logger.error(f"Error checking browser automation availability: {str(e)}")
                self.browser_automation_available = False
        self.request_timeout = 10
        self.max_retries = 2
        self.test_domains = []
        
        # Initialize settings based on the mode
        self._update_settings_for_mode()
        logger.info(f"Initialized in {self.mode} mode - Deployment environment: {self.is_deployment_env}")
    
    def _update_settings_for_mode(self):
        """Update settings based on current mode."""
        # Make sure test_domains is always properly maintained based on mode
        base_test_domains = ["localhost:5001", "localtest.me"]
        
        if self.is_production:
            # In production mode, we should NOT use test redirects or simulated results
            self.enable_test_redirects = False  # CRITICAL FIX: Must be False in production
            self.product_table_timeout = 15     # Increased timeout for production
            self.request_timeout = 15
            # Ensure partly-products-showcase.lovable.app is NOT in test_domains in production
            self.test_domains = base_test_domains.copy()
            logger.info("Production mode settings applied: test redirects disabled")
        else:
            # In development mode, enable test redirects for testing
            self.enable_test_redirects = True
            self.product_table_timeout = 5
            self.request_timeout = 5
            # Add partly-products-showcase.lovable.app to test_domains in development
            self.test_domains = base_test_domains.copy()
            self.test_domains.append("partly-products-showcase.lovable.app")
            logger.info("Development mode settings applied: test redirects enabled")
    
    @property
    def is_development(self):
        """Check if running in development mode."""
        return self.mode == "development"
    
    @property
    def is_production(self):
        """Check if running in production mode."""
        return self.mode == "production"
    
    def set_mode(self, mode):
        """
        Set the runtime mode.
        
        Args:
            mode: 'development' or 'production'
        """
        if mode not in ["development", "production"]:
            raise ValueError("Mode must be 'development' or 'production'")
            
        self.mode = mode
        self._update_settings_for_mode()
        logger.info(f"Switched to {mode} mode")
        
        return {
            "mode": self.mode,
            "enable_test_redirects": self.enable_test_redirects,
            "product_table_timeout": self.product_table_timeout,
            "request_timeout": self.request_timeout
        }
    
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