"""
Locale configuration for batch processing.
Defines supported locales and their URL parameter mappings.
"""

# Supported locales with their configurations
LOCALE_CONFIGS = {
    "en_US": {
        "country": "US",
        "language": "en",
        "url_params": "",  # Default, no parameters
        "display_name": "English (US)"
    },
    "en_CA": {
        "country": "CA", 
        "language": "en",
        "url_params": "cc=CA&lang=en",
        "display_name": "English (Canada)"
    },
    "fr_CA": {
        "country": "CA",
        "language": "fr", 
        "url_params": "cc=CA&lang=fr",
        "display_name": "Français (Canada)"
    },
    "es_MX": {
        "country": "MX",
        "language": "es",
        "url_params": "cc=MX&lang=es", 
        "display_name": "Español (México)"
    },
    "fr_FR": {
        "country": "FR",
        "language": "fr",
        "url_params": "cc=FR&lang=fr",
        "display_name": "Français (France)"
    },
    "it_IT": {
        "country": "IT",
        "language": "it",
        "url_params": "cc=IT&lang=it",
        "display_name": "Italiano (Italia)"
    },
    "ja_JP": {
        "country": "JP",
        "language": "ja",
        "url_params": "cc=JP&lang=ja",
        "display_name": "日本語 (Japan)"
    }
}

def get_supported_locales():
    """Get list of all supported locale codes."""
    return list(LOCALE_CONFIGS.keys())

def get_locale_config(locale_code: str):
    """Get configuration for a specific locale."""
    return LOCALE_CONFIGS.get(locale_code)

def generate_locale_requirements(base_requirements: dict, locale: str) -> dict:
    """
    Generate locale-specific requirements from base template.
    
    Updated fields (locale-specific):
    - country (from locale config)
    - language (from locale config)
    - campaign_code (includes country code)
    - domain (with URL parameters)
    
    Preserved fields (extracted from actual template):
    - sender_name, subject, preheader, sender_address, reply_address
    - utm_parameters
    
    Args:
        base_requirements: Base requirements dictionary (typically en_US)
        locale: Target locale code
        
    Returns:
        dict: Locale-specific requirements with structural changes only
    """
    if locale not in LOCALE_CONFIGS:
        raise ValueError(f"Unsupported locale: {locale}")
    
    locale_config = LOCALE_CONFIGS[locale]
    locale_req = base_requirements.copy()
    
    # Update locale-specific fields that change automatically
    locale_req["country"] = locale_config["country"]
    locale_req["language"] = locale_config["language"]
    
    # Update campaign_code to include country code for locale-specific validation
    base_campaign_code = base_requirements.get("campaign_code", "")
    if base_campaign_code and " - " not in base_campaign_code:
        # If campaign code doesn't already have country, add it
        locale_req["campaign_code"] = f"{base_campaign_code} - {locale_config['country']}"
    
    # Update domain with URL parameters
    base_domain = locale_req.get("domain", "")
    if locale == "en_US":
        # Default locale, no URL parameters needed
        locale_req["domain"] = base_domain
    else:
        # Add locale-specific URL parameters
        separator = "&" if "?" in base_domain else "?"
        locale_req["domain"] = f"{base_domain}{separator}{locale_config['url_params']}"
    
    return locale_req

def validate_locale_selection(selected_locales: list) -> dict:
    """
    Validate that selected locales are supported.
    
    Args:
        selected_locales: List of locale codes to validate
        
    Returns:
        dict: Validation result with status and any errors
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Handle edge cases for production deployment
    if not selected_locales:
        logger.warning("Empty locale selection received")
        return {
            "valid": False,
            "errors": "No locales selected",
            "supported_locales": get_supported_locales()
        }
    
    if not isinstance(selected_locales, list):
        logger.error(f"Invalid locale selection type: {type(selected_locales)}, expected list")
        return {
            "valid": False,
            "errors": f"Invalid locale selection format: {type(selected_locales)}",
            "supported_locales": get_supported_locales()
        }
    
    logger.info(f"Validating locale selection: {selected_locales}")
    logger.info(f"Available locale configs: {list(LOCALE_CONFIGS.keys())}")
    
    # Clean up locale codes (remove extra whitespace, handle case sensitivity)
    cleaned_locales = []
    for locale in selected_locales:
        if isinstance(locale, str):
            cleaned_locale = locale.strip()
            cleaned_locales.append(cleaned_locale)
        else:
            logger.warning(f"Non-string locale found: {locale} (type: {type(locale)})")
            cleaned_locales.append(str(locale).strip())
    
    unsupported = [locale for locale in cleaned_locales if locale not in LOCALE_CONFIGS]
    
    logger.info(f"Cleaned locales: {cleaned_locales}")
    logger.info(f"Unsupported locales found: {unsupported}")
    
    if unsupported:
        error_msg = f"Unsupported locales: {', '.join(unsupported)}"
        logger.error(error_msg)
        logger.error(f"Supported locales are: {', '.join(get_supported_locales())}")
        return {
            "valid": False,
            "errors": error_msg,
            "supported_locales": get_supported_locales(),
            "received_locales": selected_locales,
            "cleaned_locales": cleaned_locales
        }
    
    logger.info("Locale validation passed successfully")
    return {
        "valid": True,
        "errors": None,
        "supported_locales": get_supported_locales(),
        "validated_locales": cleaned_locales
    }