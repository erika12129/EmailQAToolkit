#!/bin/bash
# Email QA Automation Demo Script
# This script demonstrates the main features of the Email QA Automation tool

# Set colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}   EMAIL QA AUTOMATION TOOL - DEMONSTRATION   ${NC}"
echo -e "${BLUE}=================================================${NC}"
echo

# Check if server is running
echo -e "${BLUE}Checking if server is running...${NC}"
if ./run_qa_tests.py --check-server; then
    echo -e "${GREEN}Server is running!${NC}"
else
    echo "Server is not running. Please start the server with './run_server.sh' first."
    exit 1
fi

echo
echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}   FEATURE 1: SINGLE EMAIL VALIDATION   ${NC}"
echo -e "${BLUE}=================================================${NC}"
echo
echo "This feature validates a single email HTML file against its requirements."
echo "It checks the metadata (sender, subject, preheader) and all links with UTM parameters."
echo

read -p "Press Enter to run the single email validation demo..."

./run_qa_tests.py single --email static/sample_email.html --requirements static/sample_requirements.json

echo
echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}   FEATURE 2: LOCALIZATION VALIDATION   ${NC}"
echo -e "${BLUE}=================================================${NC}"
echo
echo "This feature validates a localized email against its localized requirements."
echo "It ensures that translated versions maintain the correct structure and parameters."
echo

read -p "Press Enter to run the localization validation demo..."

./run_qa_tests.py localize --localized-email static/sample_localized_email.html --localized-requirements static/sample_localized_requirements.json

echo
echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}   FEATURE 3: BATCH EMAIL PROCESSING   ${NC}"
echo -e "${BLUE}=================================================${NC}"
echo
echo "This feature validates multiple email HTML files against the same requirements."
echo "It's useful for testing a campaign with multiple email variations."
echo
echo "Note: This demo would need multiple sample email files. We'll skip the actual execution."
echo "The command would be:"
echo "./run_qa_tests.py batch --emails email1.html email2.html email3.html --requirements campaign_requirements.json"

echo
echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}   SUMMARY   ${NC}"
echo -e "${BLUE}=================================================${NC}"
echo
echo "The Email QA Automation tool provides:"
echo " ✓ Single email validation"
echo " ✓ Batch email processing"
echo " ✓ Localization comparison"
echo " ✓ Browser automation for link checking (when available)"
echo " ✓ Detailed reporting of validation results"
echo " ✓ Command-line and web interface options"
echo
echo "API endpoints for programmatic access:"
echo " - POST /run-qa"
echo " - POST /run-batch-qa"
echo " - POST /run-localized-qa"
echo
echo "For more information, see the README.md file."
echo
echo -e "${GREEN}Demo completed successfully!${NC}"