# Essential Files for Production Deployment

## 🚀 Core Application (7 files)
```
main.py                    # FastAPI application entry point
email_qa_enhanced.py       # Email validation engine  
cloud_browser_automation.py # Cloud browser automation
runtime_config.py          # Environment detection & config
api_endpoints.py           # API route definitions
simple_mode_switcher.py    # Batch processing endpoints
pyproject.toml            # Python dependencies
```

## 📁 Required Directories (3 folders)
```
static/                   # Frontend HTML, CSS, JavaScript
templates/               # HTML templates for testing
docs/                   # Azure deployment documentation
```

## ⚙️ Configuration (2 files)
```
domain_config.json       # Domain validation rules
locale_config.py         # Multi-language support
```

## 🗑️ Files to IGNORE in Production
```
archive/                 # Old versions and test files
test_files/             # Sample test data
test_output/            # Test results
attached_assets/        # Screenshots and debug assets
tmp/                    # Temporary files
__pycache__/           # Python cache
```

## 🔑 Required Environment Variables
```
SCRAPINGBEE_API_KEY=your_api_key_here    # Primary cloud browser service
BROWSERLESS_API_KEY=your_api_key_here    # Secondary cloud browser service (optional)
```

## 🌐 Deployment Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run application
python main.py

# Health check
curl http://localhost:5000/api/config
```

**Total Production Files: 12 files + 3 directories**
**Everything else can be ignored for deployment.**
