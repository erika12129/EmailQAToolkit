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
    
    # Also update footer_campaign_code in metadata if it exists
    if "metadata" in locale_req and "footer_campaign_code" in locale_req["metadata"]:
        footer_code = locale_req["metadata"]["footer_campaign_code"]
        if footer_code and " - " not in footer_code:
            locale_req["metadata"]["footer_campaign_code"] = f"{footer_code} - {locale_config['country']}"
    
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
    unsupported = [locale for locale in selected_locales if locale not in LOCALE_CONFIGS]
    
    if unsupported:
        return {
            "valid": False,
            "errors": f"Unsupported locales: {', '.join(unsupported)}",
            "supported_locales": get_supported_locales()
        }
    
    return {
        "valid": True,
        "errors": None,
        "supported_locales": get_supported_locales()
    }