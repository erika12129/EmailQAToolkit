# Email QA Automation System

## Overview

This is a comprehensive web application for automated QA testing of HTML emails. The system provides advanced validation and analysis capabilities for email templates, including link validation, UTM parameter verification, image alt text accessibility checks, and product table detection on destination pages.

## System Architecture

### Frontend Architecture
- **Single-page responsive web interface** built with HTML, CSS, and JavaScript
- **Static file serving** via FastAPI's StaticFiles for client assets
- **Drag-and-drop file upload** for email templates and requirements
- **Real-time validation feedback** with detailed reporting interface

### Backend Architecture
- **FastAPI-based REST API** for email validation processing
- **Mode switching capability** between development and production environments
- **Hybrid browser automation** supporting both cloud-based and local browser detection
- **Batch processing engine** for validating multiple email templates across locales
- **Flask test server** for simulating target landing pages during development

### Data Storage Solutions
- **JSON-based configuration** for domain settings and locale mappings
- **File-based storage** for email templates and requirements
- **In-memory processing** for validation results
- **Environment variable management** for API keys and configuration

### Authentication and Authorization
- **No authentication required** - designed as an internal QA tool
- **API key management** for external cloud browser services (ScrapingBee, Browserless)

## Key Components

### Email Validation Engine (`email_qa_enhanced.py`)
- **HTML parsing and analysis** using BeautifulSoup
- **Metadata extraction** (sender, subject, preheader, campaign codes)
- **Link validation** with HTTP status checking
- **UTM parameter verification** against requirements
- **Copyright year validation** with multiple format support
- **Image alt text accessibility checking**

### Browser Automation System
- **Cloud browser automation** (`cloud_browser_automation.py`) using ScrapingBee and Browserless APIs
- **Local browser automation** (`selenium_automation.py`) with Chrome/Firefox support via Selenium
- **Fallback mechanisms** when browser automation is unavailable
- **Product table detection** on React-based single-page applications

### Configuration Management
- **Runtime configuration** (`runtime_config.py`) for dynamic mode switching
- **Domain configuration** (`domain_config.json`) for site-specific validation rules
- **Locale configuration** (`locale_config.py`) for multi-language support

### API Layer
- **Main API endpoints** (`simple_mode_switcher.py`) for email validation
- **Cloud browser API** (`api_endpoints.py`) for browser automation status
- **Batch processing API** for handling multiple templates

## Data Flow

1. **Email Upload**: User uploads HTML email template and JSON requirements
2. **Parsing**: System extracts metadata, links, and content from HTML
3. **Validation**: Metadata checked against requirements, links tested for accessibility
4. **Product Detection**: Links analyzed for product table presence using browser automation
5. **Reporting**: Results compiled into structured format with pass/fail status
6. **Response**: JSON response with detailed validation results and error logs

## External Dependencies

### Cloud Browser Services
- **ScrapingBee API** for cloud-based browser automation
- **Browserless API** as alternative cloud browser service
- **Automatic fallback** to HTTP-only validation when cloud services unavailable

### Python Libraries
- **FastAPI** and **Uvicorn** for web server and API
- **Flask** for test website simulation
- **Selenium** and **webdriver-manager** for local browser automation
- **BeautifulSoup4** for HTML parsing
- **Requests** for HTTP communication
- **Trafilatura** for web content extraction

### Browser Dependencies
- **Chrome/Chromium** for local Selenium automation
- **Firefox/Gecko** as fallback browser option
- **Headless operation** optimized for server environments

## Deployment Strategy

### Development Mode
- **Local browser automation** preferred when available
- **Test website server** on port 5001 for simulating target pages
- **Debug logging** and detailed error reporting
- **Hot reload** capability for rapid development

### Production Mode
- **Cloud browser automation** prioritized for reliability
- **Optimized resource usage** without local browser dependencies
- **Error handling** with graceful degradation
- **Container-ready** with Dockerfile for cloud deployment

### Environment Detection
- **Automatic Replit detection** for cloud-hosted deployment
- **API key loading** from environment variables or secrets
- **Port configuration** (5000 for main app, 5001 for test server)
- **CORS configuration** for cross-origin requests

## Changelog
- June 12, 2025: Fixed batch QA production deployment failures
  - Enhanced locale validation robustness for production environments
  - Added graceful fallback handling for environment-specific validation issues
  - Improved error reporting with detailed debugging information
  - Modified batch processor to log warnings instead of failing on non-critical validation issues
  - Synchronized batch processing logic between development and production deployments
- June 12, 2025: Fixed production deployment batch processing issues
  - Removed blocking template validation in main.py that prevented batch processing
  - Disabled frontend validation that caused false missing template errors
  - Synchronized production deployment logic with working development environment
  - Added comprehensive debug logging for production troubleshooting
- June 12, 2025: Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.