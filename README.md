# Email QA Automation System

A comprehensive web application for automated QA testing of HTML emails, providing advanced validation and analysis capabilities for email templates, links, and UTM parameters.

## Features

- **Email Template Analysis**: Parse and validate HTML email templates
- **Metadata Validation**: Verify sender information, subject, and preheader
- **Link Validation**: Check all URLs for proper functionality and redirects
- **UTM Parameter Verification**: Validate marketing parameters in URLs (utm_source, utm_campaign, utm_medium, etc.)
- **Domain Validation**: Support for localized domains with language-specific URLs
- **Product Table Detection**: Verify the presence of product tables on destination pages
- **Multilingual Support**: Testing of localized email templates in multiple languages
- **Responsive User Interface**: Simple web-based interface for non-technical users
- **Detailed Reporting**: Clear pass/fail indications with detailed error logs

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
3. Run the application:
   ```
   python run_servers.py
   ```

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

### Email QA Module (`email_qa.py`)

Core functionality for email validation:
- HTML parsing with BeautifulSoup
- Link extraction and validation
- UTM parameter checking
- Metadata verification
- Product table detection (both with direct HTTP requests and Selenium)

### Web Server (`main.py`)

FastAPI application that:
- Provides the web interface
- Handles file uploads
- Processes validation requests
- Returns detailed validation reports

### Test Website (`test_website.py`)

Flask application that simulates destination websites:
- Handles redirects for testing
- Simulates different language domains
- Provides test pages with product tables

### Workflow Runner (`run_servers.py`)

Manages the startup and shutdown of both servers:
- Starts FastAPI on port 5000
- Starts Flask test server on port 5001
- Handles graceful shutdown

## Product Table Detection

The system checks destination pages for product display tables using two detection methods:

1. **Direct HTML Parsing**: Looks for elements with class names containing:
   - `product-table` or
   - `productListContainer`

2. **Selenium Automation**: For more complex pages, uses browser automation to:
   - Load the page with JavaScript execution
   - Check for dynamically loaded product tables
   - Verify proper rendering of product displays

## Troubleshooting

### Common Issues

- **404 Not Found**: Make sure both servers are running
- **File Upload Errors**: Check file formats (HTML for emails, JSON for requirements)
- **Link Validation Failures**: Verify URL accessibility
- **Product Table Detection Issues**: Check console logs for detailed class information

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