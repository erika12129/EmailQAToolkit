
# Product Requirements Document: Email QA Automation System - Enterprise Licensing

## Overview

This document outlines the requirements and configuration updates needed to license the Email QA Automation System to enterprise clients. The system requires specific modifications to support client-specific domains, localization patterns, and tracking requirements.

## Current System Status

- **Version**: 1.0.0 (Production Ready)
- **Deployment**: Replit Cloud Deployment
- **Architecture**: FastAPI + Cloud Browser Automation
- **Current Features**: 
  - Email HTML validation
  - Link checking with HTTP status codes
  - UTM parameter validation
  - Product table detection
  - Multi-locale support (7 languages)
  - Cloud browser automation via ScrapingBee

## Enterprise Configuration Requirements

### 1. Domain Management & Localization

#### Current State
- Domains configured in `domain_config.json`
- Basic localization support for `es`, `fr`, `de` subdomains
- Language detection from domain endings

#### Required Updates
- **Country-specific TLD support**: `domain.it`, `domain.jp`, `domain.ca`
- **Path-based language detection**: `/it/`, `/fr/`, `/jp/` preceding tracking parameters
- **Combined domain + path logic**: `domain.ca/fr/?tracking=...`

#### Implementation Requirements
```json
{
  "domains": {
    "primary": {
      "client-domain.com": {
        "localized_versions": {
          "it_IT": "client-domain.it",
          "ja_JP": "client-domain.jp",
          "fr_CA": "client-domain.ca"
        },
        "path_patterns": {
          "it_IT": "/it/",
          "ja_JP": "/jp/",
          "fr_CA": "/fr/"
        }
      }
    }
  }
}
```

### 2. Bot Whitelisting Requirements

#### Client Responsibilities
1. **Domain Whitelisting**: Add `*.replit.app` to allowed domains
2. **User-Agent Whitelisting**: Whitelist the following bot signatures:
   - `EmailQA-LinkChecker/1.0`
   - `EmailQA-ProductDetector/1.0`
   - `ScrapingBee/*` (for cloud browser automation)
   - Standard browser user agents for enhanced checks

#### System Updates Required
- Add configurable User-Agent strings per client
- Implement retry logic for bot-blocked responses
- Add client-specific rate limiting configuration

### 3. Enhanced UTM Tracking Validation

#### Current State
- Basic UTM parameter validation
- Configurable allowed values per domain

#### Required Updates
- **Supplier Identifier Component**: New UTM parameter validation
- **Character Restrictions**: 
  - **Allowed**: Alphanumeric characters, dashes (-), underscores (_)
  - **Disallowed**: Spaces, braces {}, brackets [], special characters
- **Validation Pattern**: `^[a-zA-Z0-9_-]+$`

#### Implementation Requirements
```json
{
  "utm_validation_rules": {
    "supplier_id": {
      "pattern": "^[a-zA-Z0-9_-]+$",
      "max_length": 50,
      "required": true,
      "error_message": "Supplier ID must contain only alphanumeric characters, dashes, and underscores"
    }
  }
}
```

## Technical Implementation Plan

### Phase 1: Core Configuration Updates (Week 1-2)

#### 1.1 Domain Configuration Enhancement
- Update `domain_config.json` schema
- Modify `config.py` to handle TLD + path combinations
- Add path-based language detection logic

#### 1.2 Localization Engine Updates
- Extend `locale_config.py` for new pattern support
- Update URL parsing logic in `email_qa_enhanced.py`
- Add validation for domain/path combinations

### Phase 2: UTM Validation Enhancement (Week 2-3)

#### 2.1 Supplier ID Validation
- Add new validation rules to `email_qa_enhanced.py`
- Implement regex pattern matching
- Add configurable validation rules per client

#### 2.2 Error Reporting Enhancement
- Improve error messages for UTM validation failures
- Add detailed reporting for supplier ID violations
- Update batch processing to handle new validation rules

### Phase 3: Bot Management & Whitelisting (Week 3-4)

#### 3.1 User-Agent Management
- Add configurable User-Agent strings
- Implement client-specific bot signatures
- Add User-Agent rotation for different check types

#### 3.2 Rate Limiting & Retry Logic
- Implement exponential backoff for bot-blocked requests
- Add client-specific rate limiting configuration
- Enhance error handling for access denied responses

### Phase 4: Client Onboarding Tools (Week 4-5)

#### 4.1 Configuration Generator
- Build web interface for generating client configurations
- Add validation tools for domain/path combinations
- Create testing tools for UTM validation rules

#### 4.2 Documentation & Support
- Create client setup guides
- Document whitelisting requirements
- Provide testing endpoints for validation

## Configuration Files to Update

### 1. Domain Configuration (`domain_config.json`)
```json
{
  "version": "2.0.0",
  "clients": {
    "client_name": {
      "domains": {
        "primary": {
          "client-domain.com": {
            "localized_versions": {
              "it_IT": "client-domain.it",
              "ja_JP": "client-domain.jp",
              "fr_CA": "client-domain.ca"
            },
            "path_patterns": {
              "it_IT": "/it/",
              "ja_JP": "/jp/",
              "fr_CA": "/fr/"
            },
            "utm_validation_rules": {
              "supplier_id": {
                "pattern": "^[a-zA-Z0-9_-]+$",
                "max_length": 50,
                "required": true
              }
            },
            "bot_settings": {
              "user_agents": [
                "EmailQA-LinkChecker/1.0 (ClientName)",
                "EmailQA-ProductDetector/1.0 (ClientName)"
              ],
              "rate_limit": {
                "requests_per_minute": 30,
                "burst_size": 10
              }
            }
          }
        }
      }
    }
  }
}
```

### 2. New Client Configuration Module (`client_config.py`)
- Client-specific validation rules
- Domain/path combination logic
- UTM supplier ID validation
- Bot management per client

### 3. Enhanced Validation Engine (`email_qa_enhanced.py`)
- Extended UTM validation with supplier ID rules
- Domain + path-based language detection
- Client-specific error reporting

## Enhancement Roadmap

### Phase 1: Translation Spreadsheet Integration
**Objective**: Eliminate manual copy/paste of sender names, subject lines, and preheaders by enabling direct Excel/Google Sheets import.

#### Features:
- **Spreadsheet Upload Interface**: Support for .xlsx, .csv, and Google Sheets URL import
- **Automatic Column Mapping**: Smart detection of columns containing:
  - Locale/Language codes (en_US, es_MX, fr_CA, etc.)
  - Subject lines
  - Preheader text
  - Sender names
  - Campaign codes
- **Template Validation**: Cross-reference spreadsheet data with uploaded HTML templates
- **Bulk Requirements Generation**: Auto-populate locale-specific requirements from spreadsheet data
- **Data Preview**: Show parsed spreadsheet data before processing for validation

#### Technical Implementation:
```python
# New module: spreadsheet_processor.py
class SpreadsheetProcessor:
    def parse_translation_spreadsheet(self, file_path):
        # Extract locale data from Excel/CSV
        # Map columns to metadata fields
        # Generate requirements for each locale
        pass
    
    def validate_spreadsheet_format(self, data):
        # Ensure required columns exist
        # Validate locale codes
        # Check for missing translations
        pass
```

### Phase 2: Error Analytics Dashboard
**Objective**: Transform batch QA results into actionable insights through persistent data storage and trend analysis.

#### Features:
- **SQLite Database Integration**: Store all QA results with timestamps and campaign metadata
- **Error Pattern Detection**: Identify recurring issues across campaigns and locales
- **Dashboard Visualization**: 
  - Most common validation failures
  - Error trends over time
  - Locale-specific issues
  - Campaign performance metrics
- **Automated Reporting**: Weekly/monthly QA health reports
- **Export Capabilities**: Export filtered results to Excel for stakeholder sharing

#### Database Schema:
```sql
-- qa_results.db tables
CREATE TABLE campaigns (
    id INTEGER PRIMARY KEY,
    campaign_code TEXT,
    client_name TEXT,
    created_date TIMESTAMP
);

CREATE TABLE validation_results (
    id INTEGER PRIMARY KEY,
    campaign_id INTEGER,
    locale TEXT,
    validation_type TEXT,
    status TEXT,
    error_details TEXT,
    timestamp TIMESTAMP
);

CREATE TABLE error_patterns (
    id INTEGER PRIMARY KEY,
    error_type TEXT,
    frequency INTEGER,
    last_occurrence TIMESTAMP
);
```

#### Dashboard Components:
- **Error Frequency Charts**: Bar charts showing most common validation failures
- **Locale Performance Matrix**: Heatmap of error rates by locale
- **Campaign Timeline**: Historical view of QA results per campaign
- **Export Tools**: Generate Excel reports filtered by date, locale, or error type

### Phase 3: Streamlined QA Experience
**Objective**: Simplify the user interface by consolidating single and batch QA into one unified workflow.

#### Features:
- **Unified QA Interface**: Single upload area that handles both individual and batch processing
- **Smart Template Detection**: Automatically determine if upload is single template or batch
- **Progressive Enhancement**: 
  - Start with single template → option to add more
  - Batch mode becomes default with single-template fallback
- **Simplified Navigation**: Remove separate "Single QA" and "Batch QA" modes
- **Contextual Help**: Dynamic guidance based on number of templates uploaded

#### User Experience Flow:
1. **Single Entry Point**: One "Upload Templates" button
2. **Dynamic Interface**: UI adapts based on number of files uploaded
3. **Quick Actions**: Common workflows accessible with fewer clicks
4. **Smart Defaults**: Auto-populate settings based on previous campaigns

#### Benefits:
- **Reduced Cognitive Load**: Fewer decisions for users to make
- **Faster Onboarding**: New users learn one workflow instead of two
- **Consistent Experience**: Same validation engine regardless of template count
- **Future-Proof**: Easier to add new features to single codebase

## Client Onboarding Checklist

### Pre-Deployment Requirements
- [ ] Client provides complete domain list with localization patterns
- [ ] Client confirms UTM tracking parameter names and validation rules
- [ ] Client provides whitelisting confirmation for bot access
- [ ] Client confirms rate limiting requirements

### Configuration Steps
- [ ] Generate client-specific configuration file
- [ ] Update domain patterns for TLD + path combinations
- [ ] Configure UTM validation rules including supplier ID
- [ ] Set up bot whitelisting requirements
- [ ] Configure rate limiting per client requirements

### Testing & Validation
- [ ] Test domain/path combination detection
- [ ] Validate UTM tracking with supplier ID rules
- [ ] Confirm bot access to client domains
- [ ] Test rate limiting and retry logic
- [ ] Validate multi-locale email processing

### Go-Live Requirements
- [ ] Client confirms domain whitelisting complete
- [ ] Client confirms bot whitelisting complete
- [ ] Production configuration deployed
- [ ] Monitoring and alerting configured
- [ ] Client training completed

## Success Metrics

### Technical Metrics
- **Configuration Accuracy**: 100% successful domain/path detection
- **UTM Validation**: 100% accurate supplier ID validation
- **Bot Access**: <5% blocked requests after whitelisting
- **Performance**: <2 second response time for email validation

### Business Metrics
- **Client Onboarding**: Complete setup within 5 business days
- **System Reliability**: 99.9% uptime during client usage
- **Support Tickets**: <2 configuration-related tickets per client per month

## Risk Mitigation

### Technical Risks
- **Domain Pattern Conflicts**: Implement thorough testing for domain/path combinations
- **UTM Validation Failures**: Provide clear error messages and validation tools
- **Bot Blocking**: Implement robust retry logic and client communication

### Business Risks
- **Client Onboarding Delays**: Provide comprehensive documentation and setup tools
- **Configuration Errors**: Implement validation tools and testing endpoints
- **Support Overhead**: Create self-service configuration tools

## Next Steps

1. **Development Team**: Begin Phase 1 implementation
2. **Product Team**: Finalize client onboarding process
3. **Sales Team**: Prepare client requirements gathering templates
4. **Support Team**: Develop client configuration documentation

## Conclusion

This PRD outlines the comprehensive requirements for licensing the Email QA Automation System to enterprise clients. The focus is on flexible configuration, robust validation, and seamless client onboarding while maintaining the system's current performance and reliability standards.

---

**Document Version**: 1.0  
**Last Updated**: June 17, 2025  
**Next Review**: July 1, 2025
