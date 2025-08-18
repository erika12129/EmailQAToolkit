# Email QA System - Production Deployment Guide

## Overview
This is a comprehensive Email QA automation system that validates HTML email templates, checks UTM parameters, verifies accessibility, and detects product tables on destination pages using cloud browser automation.

## Core Production Files

### 🚀 **Essential Application Files**
These files are required for production deployment:

| File | Purpose |
|------|---------|
| **`main.py`** | Main FastAPI application entry point |
| **`email_qa_enhanced.py`** | Core email validation engine |
| **`cloud_browser_automation.py`** | Cloud browser automation (ScrapingBee/Browserless) |
| **`runtime_config.py`** | Multi-cloud environment detection and configuration |
| **`api_endpoints.py`** | API route definitions |
| **`simple_mode_switcher.py`** | Enhanced batch processing endpoints |
| **`pyproject.toml`** | Python dependencies |

### 📁 **Required Directories**
| Directory | Contents |
|-----------|----------|
| **`static/`** | Frontend HTML, CSS, JavaScript |
| **`templates/`** | HTML templates for browser testing |
| **`docs/`** | Azure deployment documentation |

### ⚙️ **Configuration Files**
| File | Purpose |
|------|---------|
| **`domain_config.json`** | Domain-specific validation rules |
| **`locale_config.py`** | Multi-language support configuration |

---

## Dependencies

### Python Requirements (from pyproject.toml)
```
fastapi>=0.115.12       # Web framework
uvicorn>=0.34.1         # ASGI server
requests>=2.32.3        # HTTP client
beautifulsoup4>=4.13.4  # HTML parsing
selenium>=4.31.0        # Browser automation (fallback)
playwright>=1.52.0      # Browser automation
trafilatura>=2.0.0      # Web content extraction
pydantic>=2.11.3        # Data validation
python-multipart>=0.0.20 # File upload support
```

---

## Environment Configuration

### Multi-Cloud Support
The application automatically detects deployment environment:
- **Azure DevOps/App Service/Functions** 
- **Replit**
- **AWS Lambda/EC2**
- **Google Cloud**
- **Local development**

### Required Environment Variables

#### **ScrapingBee API** (Primary cloud browser service)
```bash
SCRAPINGBEE_API_KEY=your_api_key_here
```

#### **Browserless API** (Secondary cloud browser service)
```bash
BROWSERLESS_API_KEY=your_api_key_here
```

#### **Optional Configuration**
```bash
PORT=5000                    # Server port (default: 5000)
DEPLOYMENT_MODE=production   # Environment mode
SKIP_BROWSER_CHECK=true      # Skip local browser initialization
```

---

## Deployment Instructions

### Option 1: Azure Deployment (Recommended for Enterprise)

1. **Set Environment Variables** in Azure:
   ```bash
   az webapp config appsettings set --resource-group myRG --name myApp --settings SCRAPINGBEE_API_KEY="your_key"
   ```

2. **Deploy Application**:
   - Use Azure DevOps pipeline
   - Or deploy directly from GitHub
   - Ensure port 8000 is configured for Azure Container Apps

3. **Health Check Endpoint**: `/api/config`

### Option 2: Replit Deployment

1. **Add Secrets** in Replit:
   - Go to Secrets tab
   - Add `SCRAPINGBEE_API_KEY` with your API key

2. **Deploy**:
   - Click Deploy button in Replit
   - Application runs on port 5000

### Option 3: Docker Deployment

1. **Build Container**:
   ```bash
   docker build -t email-qa-system .
   ```

2. **Run Container**:
   ```bash
   docker run -e SCRAPINGBEE_API_KEY=your_key -p 5000:5000 email-qa-system
   ```

---

## API Key Setup

### ScrapingBee (Primary)
1. Sign up at https://scrapingbee.com
2. Get API key from dashboard
3. Set as environment variable: `SCRAPINGBEE_API_KEY`

### Browserless (Fallback)
1. Sign up at https://browserless.io
2. Get API key from dashboard  
3. Set as environment variable: `BROWSERLESS_API_KEY`

---

## Application Architecture

### Core Components

1. **FastAPI Server** (`main.py`)
   - Serves API endpoints
   - Handles file uploads
   - Manages static assets

2. **Validation Engine** (`email_qa_enhanced.py`)
   - HTML parsing and metadata extraction
   - UTM parameter validation
   - Copyright year checking
   - Image alt text validation
   - Campaign code verification

3. **Cloud Browser System** (`cloud_browser_automation.py`)
   - Product table detection in SPAs
   - JavaScript rendering
   - Fallback between ScrapingBee/Browserless

4. **Batch Processing** (`simple_mode_switcher.py`)
   - Multi-locale email validation
   - Automatic locale detection
   - Parallel processing

### Data Flow
```
Email Upload → Metadata Extraction → Link Validation → Product Table Detection → Report Generation
```

---

## Key Features

### ✅ **Email Validation**
- HTML structure analysis
- UTM parameter verification
- Copyright year validation (© and @ formats)
- Image accessibility checking
- Campaign code format validation

### ✅ **Multi-Locale Support**
- 7 languages: en_US, en_CA, fr_CA, es_MX, fr_FR, it_IT, ja_JP
- Automatic locale detection from HTML
- Locale-specific validation rules

### ✅ **Product Table Detection**
- React SPA compatibility
- Traditional website support
- Cloud browser automation
- Graceful fallback handling

### ✅ **Batch Processing**
- Multiple file upload
- Parallel validation
- Progress tracking
- Detailed reporting

---

## Files to IGNORE in Production

### 🗑️ **Test and Development Files**
```
archive/                    # Old versions and test files
test_files/                 # Sample test data
test_output/                # Test results
attached_assets/            # Screenshots and debug assets
tmp/                        # Temporary files
__pycache__/               # Python cache files
*.pyc                      # Compiled Python files
```

### 🗑️ **Legacy and Superseded Files**
```
browser_detection.py       # Superseded by runtime_config.py
browser_automation.py      # Superseded by cloud_browser_automation.py
selenium_automation.py     # Superseded by cloud browser APIs
run_servers.py            # Development-only dual server setup
run_servers_prod.py       # Development-only dual server setup
config.py                 # Old configuration system
batch_processor.py        # Superseded by simple_mode_switcher.py
```

### 🗑️ **Test and Debug Files**
```
cloud_api_test.py
cloud_detection_test.py
demo_cloud_detector.py
direct_cloud_test_server.py
test_*.py                 # All test files
test_*.html              # Test HTML files
*_debug.json            # Debug output files
*_response.json         # API response logs
```

---

## Troubleshooting

### Common Issues

1. **"Browser automation unavailable"**
   - Check `SCRAPINGBEE_API_KEY` environment variable
   - Verify API key validity
   - Check ScrapingBee account limits

2. **"Product table detection failed"**
   - Ensure cloud browser API is configured
   - Check network connectivity
   - Verify destination URL accessibility

3. **"Validation errors"**
   - Check `domain_config.json` for domain-specific rules
   - Verify HTML email structure
   - Ensure UTM parameters match requirements

### Health Check
- **Endpoint**: `GET /api/config`
- **Expected**: `200 OK` with configuration object
- **Key Fields**: `browser_automation_available: true`

---

## Security Considerations

1. **API Keys**: Store in environment variables, never in code
2. **CORS**: Configure appropriately for production domain
3. **File Uploads**: Validate file types and sizes
4. **Network**: Restrict outbound connections if needed

---

## Monitoring and Logging

### Log Levels
- **INFO**: Application startup, configuration loading
- **WARNING**: Fallback browser usage, deprecated features
- **ERROR**: Validation failures, API errors

### Key Metrics to Monitor
- API response times
- Email validation success rates
- Cloud browser API usage
- Error rates by endpoint

---

This deployment guide provides everything needed for a clean production handoff. Focus on the "Essential Application Files" section for core deployment requirements.
