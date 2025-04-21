# Email QA Automation Tool

A comprehensive tool for automating QA testing of HTML emails. This tool validates email metadata, links, and UTM parameters against requirements.

## Features

- Validate email sender, subject, and preheader text
- Check links for correct UTM parameters
- Compare localized emails against parent versions
- Batch process multiple emails with a single set of requirements
- Command-line interface for automation
- Web interface for user-friendly operation

## Getting Started

### Prerequisites

- Python 3.7 or higher
- Dependencies: FastAPI, Uvicorn, Beautiful Soup 4, Requests, Selenium (optional for advanced link checking)

### Installation

1. Clone this repository
2. Install required dependencies:
   ```
   pip install fastapi uvicorn python-multipart beautifulsoup4 requests selenium webdriver-manager
   ```

### Running the Server

Start the server using the provided script:

```bash
./run_server.sh
```

This will start the server on port 5000. The server provides both a web interface and API endpoints for email validation.

## Usage

### Web Interface

Open your browser and navigate to [http://localhost:5000](http://localhost:5000). The web interface provides three main sections:

1. **Single Email QA**: Validate a single email against requirements
2. **Batch Processing**: Validate multiple emails against the same requirements
3. **Localization QA**: Compare localized emails with their parent versions

### Command-Line Interface

The `run_qa_tests.py` script provides a convenient command-line interface for testing.

#### Check Server Status

```bash
./run_qa_tests.py --check-server
```

#### Single Email Validation

```bash
./run_qa_tests.py single --email path/to/email.html --requirements path/to/requirements.json
```

#### Batch Validation

```bash
./run_qa_tests.py batch --emails path/to/email1.html path/to/email2.html --requirements path/to/requirements.json
```

#### Localization Validation

```bash
./run_qa_tests.py localize --localized-email path/to/localized.html --localized-requirements path/to/localized_req.json
```

With parent comparison:

```bash
./run_qa_tests.py localize --localized-email path/to/localized.html --localized-requirements path/to/localized_req.json --parent-email path/to/parent.html --parent-requirements path/to/parent_req.json --compare
```

## API Endpoints

The tool provides several API endpoints for programmatic access:

- `POST /run-qa`: Validate a single email
- `POST /run-batch-qa`: Validate multiple emails
- `POST /run-localized-qa`: Validate localized emails

Refer to the code comments for detailed API documentation.

## Requirements Format

The requirements should be provided as a JSON file with the following structure:

```json
{
  "sender": "marketing@company.com",
  "subject": "Special Discount - 25% Off",
  "preheader": "Limited time offer: 25% discount on all products! Shop now and save!",
  "utm_parameters": {
    "utm_source": "email",
    "utm_medium": "marketing",
    "utm_campaign": "special_offer"
  }
}
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.