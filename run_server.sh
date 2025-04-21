#!/bin/bash
# Start the FastAPI server on port 5000

echo "================================================="
echo "   EMAIL QA AUTOMATION TOOL - SERVER STARTUP    "
echo "================================================="
echo
echo "Starting server on port 5000..."
echo "The server provides both a web interface and API endpoints."
echo
echo "Web Interface: http://localhost:5000"
echo "API Endpoints:"
echo " - POST /run-qa             (Single Email QA)"
echo " - POST /run-batch-qa       (Batch Processing)"
echo " - POST /run-localized-qa   (Localization QA)"
echo
echo "Starting server now..."
echo "================================================="
echo

python main.py