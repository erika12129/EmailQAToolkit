# Email QA Automation System

## Overview

This is a comprehensive web application for automated QA testing of HTML emails. The system provides advanced validation and analysis capabilities for email templates, including link validation, UTM parameter verification, image alt text accessibility checks, and product table detection on destination pages.

## System Architecture

### Frontend Architecture
- **Single-page responsive web interface** using HTML, CSS, and JavaScript
- **Static file serving** for email templates and assets
- **Real-time validation feedback** with detailed pass/fail indicators
- **Batch processing UI** for multiple locale testing
- **Cloud browser configuration interface** for API key management

### Backend Architecture
- **FastAPI-based API service** for processing email validation requests
- **Flask test server** for simulating target landing pages during development
- **Modular validation engine** with pluggable components
- **Hybrid browser automation** supporting both local and cloud-based detection
- **Runtime configuration system** for development/production mode switching

### Data Storage Solutions
- **JSON-based configuration** for domain settings and locale mappings
- **File-based template storage** for email HTML and requirements
- **In-memory caching** for validation results and browser detection
- **No persistent database** - stateless operation

## Key Components

### Email Validation Engine (`email_qa_enhanced.py`)
- **HTML parsing and metadata extraction** using BeautifulSoup
- **Link validation** with HTTP status checking
- **UTM parameter verification** against requirements
- **Copyright year validation** (supports both © and @ formats)
- **Image alt text accessibility checking**
- **Campaign code validation** with dynamic prefix handling

### Browser Automation System
- **Local browser automation** using Selenium (Chrome/Firefox)
- **Cloud browser automation** via ScrapingBee and Browserless APIs
- **Fallback mechanisms** for environments without browser support
- **Product table detection** in React SPAs and traditional websites

### Configuration Management
- **Runtime mode switching** between development and production
- **Domain-specific configuration** via `domain_config.json`
- **Locale support** for 7 languages (en_US, en_CA, fr_CA, es_MX, fr_FR, it_IT, ja_JP)
- **API key management** for cloud browser services

### Batch Processing Engine
- **Multi-locale template validation** with parallel processing
- **Dynamic locale detection** from HTML lang attributes
- **Automated requirements generation** based on locale patterns
- **Progress tracking** and detailed reporting

## Data Flow

1. **Email Template Upload**: User uploads HTML email template(s) via web interface
2. **Requirements Processing**: JSON requirements are parsed and validated against locale configurations
3. **Metadata Extraction**: Email HTML is parsed to extract sender, subject, preheader, and other metadata
4. **Link Analysis**: All URLs are extracted and validated for HTTP status and UTM parameters
5. **Product Table Detection**: Destination pages are analyzed using browser automation (local or cloud)
6. **Image Validation**: Standalone images are checked for alt text accessibility
7. **Report Generation**: Comprehensive validation results are compiled and returned to user

## External Dependencies

### Cloud Browser APIs
- **ScrapingBee**: Primary cloud browser automation service
- **Browserless**: Secondary cloud browser automation service
- **API key configuration**: Environment variables or Replit secrets

### Local Browser Automation
- **Selenium WebDriver**: For local browser automation
- **Chrome/Chromium**: Primary browser for automation
- **Firefox/Gecko**: Fallback browser option
- **WebDriver Manager**: Automatic driver installation

### Web Scraping and Analysis
- **Trafilatura**: Web content extraction
- **BeautifulSoup4**: HTML parsing and manipulation
- **Requests**: HTTP client for link validation

## Deployment Strategy

### Development Mode
- **Local Flask test server** on port 5001 for simulating target pages
- **FastAPI main server** on port 5000 for the application
- **Hot-reload capabilities** for rapid development
- **Comprehensive logging** for debugging

### Production Mode
- **Single FastAPI server** deployment
- **Cloud Run compatibility** for scalable deployment
- **Environment variable configuration** for API keys
- **Graceful degradation** when browser automation is unavailable

### Replit Deployment
- **Automatic dependency management** via pyproject.toml
- **Secrets management** for API keys
- **Port configuration** for external access
- **Workflow automation** for streamlined deployment

## Recent Changes

- **June 13, 2025**: RESOLVED production deployment issues and JavaScript errors
  - Fixed deployment port configuration to use port 8000 as required by Cloud Run
  - Added comprehensive error handling for Chrome WebDriver initialization issues
  - Set production environment variables for optimized deployment mode
  - Optimized application startup time by removing expensive browser initialization operations
  - Created dedicated deployment script (deploy.py) with comprehensive error handling
  - Fixed JavaScript syntax errors in template detection results processing
  - Added robust null checks and try-catch blocks to prevent production errors

- **June 13, 2025**: RESOLVED 422 error in batch QA functionality  
  - Enhanced error logging with detailed JSON validation messages
  - Fixed batch validation endpoint parameter handling
  - Added comprehensive debugging information for troubleshooting
  - Batch QA now returns proper 400 status codes with specific error details

- **June 13, 2025**: Enhanced batch QA interface simplification and field width improvements completed
  - Removed dropdown filter completely to simplify interface after complexity issues
  - Increased locale-specific input field widths to 600px to accommodate up to 100 characters
  - Added responsive design with max-width: 100% for mobile compatibility
  - Streamlined export functionality works correctly with proper JSON format
  - Maintained clean, user-friendly interface focused on core functionality
  - Auto-population from domain_config.json and template data working reliably

- **June 13, 2025**: RESOLVED critical campaign code validation bug in enhanced batch system
  - Fixed frontend custom requirements generation to include footer_campaign_code in metadata section
  - Enhanced batch system now properly formats campaign codes with country suffix ("ABC2505 - US")
  - Updated static/index.html to include metadata object with footer_campaign_code field
  - Campaign code validation now shows PASS instead of FAIL for correct format matches
  - Enhanced metadata validation logic in email_qa_enhanced.py for consistent formatting

- **June 13, 2025**: Enhanced batch processing system completed with UI improvements
  - Multi-file upload with automatic locale detection from HTML lang attributes and campaign codes
  - Fixed step progression to show all 5 steps: Upload → Locale Detection → Global Settings → Locale Content → Process
  - Added intermediate "waiting for inputs" status messages for better user experience
  - Simplified requirements interface with individual forms per detected locale
  - Global settings form for sender addresses, campaign codes, and UTM parameters
  - Automatic domain URL generation with locale-specific parameters
  - Support for 7 locales: en_US, en_CA, fr_CA, es_MX, fr_FR, it_IT, ja_JP
  - Fixed file display issues and locale API loading problems

## Changelog

- June 13, 2025. Enhanced batch QA system with multi-file upload and automatic locale detection
- June 13, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.