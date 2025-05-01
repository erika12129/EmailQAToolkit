"""
Configuration module for the Email QA System.
Handles environment-specific settings and domain configurations.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Default configuration paths
DEFAULT_CONFIG_PATH = "domain_config.json"

class Config:
    """Configuration manager for the Email QA System."""
    
    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH):
        """
        Initialize the configuration.
        
        Args:
            config_path: Path to the configuration JSON file
        """
        self.config_path = config_path
        self.config_data = {}
        self.load_config()
        
        # Determine environment (development or production)
        self.environment = os.environ.get("EMAIL_QA_ENV", "development").lower()
        logger.info(f"Running in {self.environment} environment")
    
    def load_config(self) -> None:
        """Load configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                self.config_data = json.load(f)
            logger.info(f"Loaded configuration from {self.config_path}")
        except FileNotFoundError:
            logger.warning(f"Configuration file {self.config_path} not found. Using default settings.")
            self.config_data = {
                "version": "1.0.0",
                "domains": {
                    "primary": {},
                    "test": {
                        "localhost:5001": {
                            "product_table_check": True,
                            "expected_classes": ["product-table", "productListContainer"],
                            "is_test_domain": True
                        }
                    }
                },
                "global_settings": {
                    "enable_redirect_to_test": True,
                    "default_language": "en",
                    "max_retries": 3,
                    "request_timeout": 10
                }
            }
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON in configuration file {self.config_path}")
            raise
    
    def reload_config(self) -> None:
        """Reload configuration from disk."""
        self.load_config()
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"
    
    @property
    def enable_test_redirects(self) -> bool:
        """Check if test redirects are enabled."""
        if self.is_production:
            # In production, always disable redirects unless explicitly enabled
            return False
        # In development, check the setting but default to True
        return self.config_data.get("global_settings", {}).get("enable_redirect_to_test", True)
    
    @property
    def domain_list(self) -> Dict[str, Any]:
        """Get all configured domains."""
        return self.config_data.get("domains", {})
    
    @property
    def primary_domains(self) -> Dict[str, Any]:
        """Get all primary (production) domains."""
        return self.domain_list.get("primary", {})
    
    @property
    def test_domains(self) -> Dict[str, Any]:
        """Get all test domains."""
        return self.domain_list.get("test", {})
    
    def get_domain_config(self, domain: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific domain.
        
        Args:
            domain: The domain to lookup
            
        Returns:
            Domain configuration or None if not found
        """
        # Check primary domains
        if domain in self.primary_domains:
            return self.primary_domains[domain]
        
        # Check test domains
        if domain in self.test_domains:
            return self.test_domains[domain]
        
        # Check localized versions of primary domains
        for primary_domain, config in self.primary_domains.items():
            localized = config.get("localized_versions", {})
            for _, localized_domain in localized.items():
                if domain == localized_domain:
                    return config
        
        return None
    
    def is_test_domain(self, domain: str) -> bool:
        """
        Check if a domain is configured as a test domain.
        
        Args:
            domain: The domain to check
            
        Returns:
            True if this is a test domain, False otherwise
        """
        domain_config = self.get_domain_config(domain)
        if domain_config:
            return domain_config.get("is_test_domain", False)
        return False
    
    def should_check_product_tables(self, domain: str) -> bool:
        """
        Check if product table detection should be performed for this domain.
        
        Args:
            domain: The domain to check
            
        Returns:
            True if product table checks should be performed, False otherwise
        """
        domain_config = self.get_domain_config(domain)
        if domain_config:
            return domain_config.get("product_table_check", False)
        return False
    
    def get_expected_classes(self, domain: str) -> List[str]:
        """
        Get the expected CSS classes for product tables on this domain.
        
        Args:
            domain: The domain to check
            
        Returns:
            List of expected class names
        """
        domain_config = self.get_domain_config(domain)
        if domain_config:
            return domain_config.get("expected_classes", ["product-table", "productListContainer"])
        return ["product-table", "productListContainer"]
    
    def get_localized_domain(self, primary_domain: str, language_code: str) -> Optional[str]:
        """
        Get the localized version of a domain for a specific language.
        
        Args:
            primary_domain: The primary domain
            language_code: The language code (e.g. 'es', 'fr')
            
        Returns:
            Localized domain or None if not found
        """
        domain_config = self.get_domain_config(primary_domain)
        if domain_config:
            localized = domain_config.get("localized_versions", {})
            return localized.get(language_code)
        return None
    
    def get_locale_rules(self, language_code: str) -> Dict[str, Any]:
        """
        Get localization rules for a specific language.
        
        Args:
            language_code: The language code (e.g. 'es', 'fr')
            
        Returns:
            Localization rules for the language
        """
        localization = self.config_data.get("localization_rules", {})
        return localization.get(language_code, {})
    
    def get_allowed_utm_parameters(self, domain: str) -> Dict[str, List[str]]:
        """
        Get allowed UTM parameters for a domain.
        
        Args:
            domain: The domain to check
            
        Returns:
            Dictionary of allowed UTM parameters
        """
        domain_config = self.get_domain_config(domain)
        if domain_config:
            return domain_config.get("allowed_utm_parameters", {})
        return {}
    
    @property
    def max_retries(self) -> int:
        """Get maximum number of retries for HTTP requests."""
        return self.config_data.get("global_settings", {}).get("max_retries", 3)
    
    @property
    def request_timeout(self) -> int:
        """Get timeout for HTTP requests in seconds."""
        return self.config_data.get("global_settings", {}).get("request_timeout", 10)
    
    @property
    def default_language(self) -> str:
        """Get default language code."""
        return self.config_data.get("global_settings", {}).get("default_language", "en")


# Create a global instance of the config
config = Config()