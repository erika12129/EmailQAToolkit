# Email QA Automation System

## Overview

The Email QA Automation System is a comprehensive web application designed for automated quality assurance testing of HTML email templates. It provides advanced validation capabilities including metadata verification, link checking, UTM parameter validation, and product table detection. The system is built with a FastAPI backend and a responsive web frontend, supporting both local browser automation and cloud-based testing services.

## System Architecture

### Frontend Architecture
- **Single-page web application** using vanilla HTML, CSS, and JavaScript
- **Responsive design** optimized for desktop and mobile use
- **Real-time validation feedback** with clear pass/fail indicators
- **File upload interface** for email templates and requirements
- **Batch processing support** for multiple locales

### Backend Architecture
- **FastAPI framework** for RESTful API endpoints
- **Modular design** with separate modules for different validation types
- **Async processing** for handling multiple concurrent validations
- **Multi-mode operation** supporting development and production environments
- **Runtime configuration** allowing mode switching without restarts

### Browser Automation Strategy
- **Hybrid approach** combining local Selenium and cloud browser APIs
- **Selenium WebDriver** for local Chrome/Firefox automation when available
- **Cloud browser services** (ScrapingBee, Browserless) for environments without local browsers
- **Intelligent fallback** to HTTP-only validation when browsers unavailable

## Key Components

### Email Validation Engine (`email_qa_enhanced.py`)
- Parses HTML email templates using BeautifulSoup
- Validates metadata (sender, subject, preheader)
- Checks all links for functionality and redirects
- Verifies UTM parameters against requirements
- Detects copyright year validation
- Supports localized domain configurations

### Browser Automation (`selenium_automation.py`, `cloud_browser_automation.py`)
- **Local automation**: Uses Selenium with Chrome/Firefox for product table detection
- **Cloud automation**: Integrates with ScrapingBee and Browserless APIs
- **React SPA support**: Specialized JavaScript execution for modern web applications
- **Timeout handling**: Configurable timeouts for slow-loading pages

### Batch Processing (`batch_processor.py`)
- Processes multiple email templates across different locales
- Generates locale-specific requirements automatically
- Provides progress tracking and error handling
- Supports parallel processing for efficiency

### Configuration Management
- **Runtime configuration** (`runtime_config.py`) for mode switching
- **Domain configuration** (`domain_config.json`) for URL parameter mappings
- **Locale configuration** (`locale_config.py`) for internationalization support
- **Environment detection** for Replit and deployment environments

## Data Flow

1. **Email Upload**: User uploads email HTML file and requirements JSON
2. **Parsing**: System extracts metadata and links from email template
3. **Validation**: Each component (metadata, links, UTM parameters) validated against requirements
4. **Browser Checks**: Product table detection using available browser automation
5. **Result Compilation**: All validation results aggregated into comprehensive report
6. **Response**: JSON response with detailed pass/fail status for each check

## External Dependencies

### Browser Automation APIs
- **ScrapingBee**: Cloud browser automation with JavaScript execution
- **Browserless**: Headless Chrome API for web scraping
- **Selenium WebDriver**: Local browser automation framework

### Python Libraries
- **FastAPI**: Web framework for API development
- **BeautifulSoup4**: HTML parsing and manipulation
- **Selenium**: Browser automation
- **Requests**: HTTP client library
- **Trafilatura**: Web content extraction
- **Flask**: Test website server

### Development Tools
- **Webdriver Manager**: Automatic browser driver management
- **Playwright**: Alternative browser automation (available but not primary)

## Deployment Strategy

### Environment Detection
- **Replit Environment**: Automatic detection using `REPL_ID` environment variable
- **Production Mode**: Optimized for cloud deployment with reduced resource usage
- **Development Mode**: Full feature set including test website server

### Port Configuration
- **Port 5000**: Main FastAPI application
- **Port 5001**: Flask test website (development only)
- **Port 3000-3003**: External port mappings for Replit deployment

### Browser Availability Handling
- **Automatic fallback**: Graceful degradation when browsers unavailable
- **Cloud API prioritization**: Prefers cloud services in containerized environments
- **HTTP-only mode**: Basic validation when no browser automation available

## Changelog

- June 13, 2025. Initial setup

## User Preferences

Preferred communication style: Simple, everyday language.