# Email QA Automation System

A comprehensive web application for automated QA testing of HTML emails, providing advanced validation and analysis capabilities for email templates, links, UTM parameters, image alt text accessibility, and product table detection with bot protection awareness.

## Features

- **Email Template Analysis**: Parse and validate HTML email templates
- **Metadata Validation**: Verify sender information, subject, and preheader
- **Link Validation**: Check all URLs for proper functionality and redirects
- **UTM Parameter Verification**: Validate marketing parameters in URLs (utm_source, utm_campaign, utm_medium, etc.)
- **Domain Validation**: Support for localized domains with language-specific URLs
- **Product Table Detection**: Verify the presence of product tables on destination pages
- **Image Alt Text Validation**: Verify standalone images have appropriate alt text for accessibility
- **Bot Detection**: Identify when target websites are blocking automated checks
- **Multilingual Support**: Testing of localized email templates in multiple languages
- **Responsive User Interface**: Simple web-based interface for non-technical users
- **Detailed Reporting**: Clear pass/fail indications with detailed error logs
- **Configurable Timeouts**: Adjustable timeouts for handling slow-loading pages

## System Architecture

The application consists of:

- **Frontend**: Single-page responsive web interface (HTML, CSS, JavaScript)
- **Backend API**: FastAPI service for processing email validation requests
- **Testing Server**: Flask-based server for simulating target landing pages
- **Automation Tools**: Python utilities for email parsing and validation

## Setup and Installation

### Requirements

- Python 3.7 or higher
- Required Python packages (see requirements.txt):
  - fastapi
  - uvicorn
  - flask
  - requests
  - beautifulsoup4
  - python-multipart
  - selenium (for product table detection)
  - trafilatura (for web content extraction)
  - webdriver-manager (for headless browser automation)

### Installation

1. Clone this repository
2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Run the application in development mode:
   ```
   python run_servers.py
   ```
   
### Production Deployment

The application supports both development and production environments:

1. **Development Mode**: Uses localhost redirects for testing, providing a complete testing environment on a single machine.
   ```
   python run_servers_prod.py
   ```

2. **Production Mode**: Disables localhost redirects and connects directly to actual domains.
   ```
   python run_servers_prod.py --production
   ```

3. **Environment Variables**:
   - `EMAIL_QA_ENV`: Set to `production` to run in production mode
   
4. **Domain Configuration**:
   The application uses a `domain_config.json` file to determine how domains are handled:
   - Primary domains: Real domains that should be accessed directly in production
   - Test domains: Domains that should be redirected to the test server
   - Localized versions: Language-specific variants of primary domains
   
   Example domain configuration:
   ```json
   {
     "version": "1.0.0",
     "domains": {
       "primary": {
         "example.com": {
           "product_table_check": true,
           "expected_classes": ["product-table", "productListContainer"],
           "localized_versions": {
             "es": "example.es",
             "fr": "example.fr"
           },
           "allowed_utm_parameters": {
             "utm_source": ["email", "newsletter"],
             "utm_medium": ["marketing", "promotional"],
             "utm_campaign": ["*"],
             "utm_content": ["*"]
           }
         }
       },
       "test": {
         "localhost:5001": {
           "product_table_check": true,
           "expected_classes": ["product-table", "productListContainer"],
           "is_test_domain": true
         }
       }
     },
     "global_settings": {
       "enable_redirect_to_test": true,
       "default_language": "en",
       "max_retries": 3,
       "request_timeout": 10
     }
   }
   ```
   
5. **API Endpoint Options**:
   - `/run-qa?force_production=true`: Run a single validation in production mode
   - `/reload-config`: Reload the domain configuration without restarting
   - `/config`: View current configuration

## Usage Guide

### Basic Usage

1. Open the application in a web browser at http://localhost:5000
2. Upload an HTML email file
3. Upload a requirements JSON file (or use the form to specify requirements)
4. Click "Validate Email" to run the QA check
5. Review detailed results in the web interface

### Validation Requirements

The system validates emails against a set of requirements provided in JSON format:

```json
{
  "metadata": {
    "sender_name": "Example Company",
    "sender_address": "marketing@example.com",
    "reply_address": "support@example.com",
    "subject": "Special Offer Inside!",
    "preheader": "Don't miss our exclusive deals"
  },
  "utm_parameters": {
    "utm_source": "email",
    "utm_medium": "marketing",
    "utm_campaign": "spring_sale_2025",
    "utm_content": "product_announcement"
  },
  "localization": {
    "default_domain": "example.com",
    "local_domains": {
      "es": "example.es",
      "fr": "example.fr"
    }
  }
}
```

### Sample Files

The `attached_assets` directory contains sample files for testing:
- `Replit_test_email.html`: Sample email template (English)
- `Replit_test_es_MX.html`: Sample email template (Spanish)
- `sample_requirements.json`: Example validation requirements
- `sample_requirements_esMX.json`: Example requirements for Spanish validation
- `product_class_test.html`: Test file with product table classes

## Key Components

### Email QA Module (`email_qa.py` and `email_qa_prod.py`)

Core functionality for email validation:
- HTML parsing with BeautifulSoup
- Link extraction and validation
- UTM parameter checking
- Metadata verification
- Image alt text extraction and validation
- Product table detection (both with direct HTTP requests and Selenium)

The `email_qa_prod.py` version adds:
- Environment-aware processing
- Domain-specific validation rules
- Production-ready error handling
- Configurable domain redirects

### Web Server (`main.py` and `main_prod.py`)

FastAPI application that:
- Provides the web interface
- Handles file uploads
- Processes validation requests
- Returns detailed validation reports

The `main_prod.py` version adds:
- Environment indicator in the UI
- Additional API endpoints for configuration
- Production/development toggle
- Enhanced error handling

### Configuration System (`config.py` and `domain_config.json`)

Configuration management for the application:
- Environment detection (production vs development)
- Domain-specific processing rules
- Localization support
- Configurable timeouts and retries

### Test Website (`test_website.py`)

Flask application that simulates destination websites:
- Handles redirects for testing
- Simulates different language domains
- Provides test pages with product tables

### Workflow Runner (`run_servers.py` and `run_servers_prod.py`)

Manages the startup and shutdown of both servers:
- Starts FastAPI on port 8000 (production) or 5000 (development)
- Starts Flask test server on port 5001
- Handles graceful shutdown

The `run_servers_prod.py` version adds:
- Command-line arguments for production mode
- Environment variable configuration
- Improved process management

## Product Table Detection

The system checks destination pages for product display tables using an improved detection mechanism:

1. **Direct HTML Parsing**: Checks for elements with class names matching specific patterns:
   - Multiple pattern matching with smart detection for variant class names
   - Support for configurable class name patterns per domain
   - Pattern-based approach rather than exact string matching for more flexible detection

2. **Bot Detection**: Identifies when websites are blocking automated checks:
   - Detects when a website is blocking the automated request
   - Provides clear feedback that bot protection is in place
   - Prevents false negatives when product tables can't be accessed due to bot protection

3. **Configurable Timeouts**: Adjustable timeout settings:
   - Options for 5s, 10s, 30s, and 60s timeouts
   - Handles slow-loading sites and complex product pages
   - Prevents hanging the main application during detection

## Current System Architecture

The Email QA System features a streamlined architecture with cloud browser integration for product detection:

1. **Core Components**:
   - `simple_mode_switcher.py`: Main FastAPI application with integrated mode switching
   - `email_qa_enhanced.py`: Improved email validation with better error handling
   - `runtime_config.py`: Configuration manager with mode switching capability
   - `run_servers.py`: Unified server launcher with simple workflow
   - `cloud_browser_automation.py`: Cloud-based browser automation for product table detection
   - `browser_automation.py`: Browser automation wrapper with fallback handling
   - `api_endpoints.py`: API endpoints for cloud browser configuration

2. **Active Files**:
   - **FastAPI Application**: `simple_mode_switcher.py`, `main.py`
   - **Email Validation**: `email_qa_enhanced.py`
   - **Configuration**: `runtime_config.py`, `config.py`
   - **Browser Automation**: `browser_automation.py`, `browser_detection.py`
   - **Cloud Integration**: `cloud_browser_automation.py`, `cloud_api_test.py`
   - **Test Website**: `test_website.py`
   - **Server Management**: `run_servers.py`, `run_servers_prod.py`

3. **Key Features**:
   - **Cloud Browser Integration**: Uses ScrapingBee API for reliable browser automation in cloud environments
   - **Two-Phase Validation**: Fast initial link validation followed by optional product table detection
   - **Selective Product Table Checking**: User-selectable URLs for product table validation
   - **Image Alt Text Validation**: Extracts standalone images and validates proper alt text for accessibility
   - **Configurable Timeouts**: User-adjustable timeout settings for product table checks
   - **UI Improvements**: Clearer status indicators and more intuitive workflow

4. **Running the System**:
   ```bash
   # Start the application (development mode)
   python run_servers.py
   
   # Start the application (production mode)
   python run_servers_prod.py
   ```

5. **API Endpoints**:
   - `/run-qa`: Main validation endpoint with multiple options
   - `/check-product-tables`: Dedicated endpoint for product table checking
   - `/set-mode/development` or `/set-mode/production`: Mode switching
   - `/config`: View current configuration
   - `/api/set-cloud-api-key`: Set a cloud browser API key
   - `/api/test-cloud-api`: Test a cloud browser API key

6. **Product Table Detection**:
   - Focused on specific class-based detection:
     - Classes starting with "product-table" (product-table*)
     - Classes ending with "productListContainer" (*productListContainer)
     - "noPartsPhrase" class for negative detection
   - Cloud browser automation for environments where local browsers aren't available
   - Fast detection with configurable timeouts to prevent UI hanging
   
7. **Image Alt Text Validation**:
   - Extracts all standalone images not contained within links
   - Validates presence of alt text attributes for accessibility compliance
   - Displays warning icons (⚠️) for images missing alt text 
   - Shows image thumbnails alongside location and dimension information
   - Provides count of accessibility warnings in the interface

## Troubleshooting

### Common Issues

- **404 Not Found**: Make sure both servers are running
- **File Upload Errors**: Check file formats (HTML for emails, JSON for requirements)
- **Link Validation Failures**: Verify URL accessibility 
- **Bot Detection Messages**: This indicates the website is blocking automated requests, not a system error
- **Product Table Detection Issues**: Check if the appropriate checkboxes are selected before running detection
- **Missing Image Alt Text Warnings**: These indicate accessibility issues that should be fixed in the email HTML
- **Image Section Not Appearing**: Email may not contain any standalone images (images inside links appear in the Links section)
- **Slow Detection Responses**: Try increasing the timeout setting for slow-loading sites
- **Production Mode Failures**: Check domain configuration in `domain_config.json`

## Development and Extension

### Adding New Features

1. **New Validation Rules**: Add to the `validate_email` function in `email_qa.py`
2. **UI Enhancements**: Modify the HTML/CSS/JS in `static/index.html`
3. **Additional Test Pages**: Add routes to `test_website.py`

### Testing

Run the included test scripts:
- `simple_test.py`: Basic app functionality
- `test_api.py`: API response validation
- `spanish_test.py`: Localization testing
- `test_product_tables.py`: Product table detection

## License

[Specify license information]

## Contributing

[Contribution guidelines]