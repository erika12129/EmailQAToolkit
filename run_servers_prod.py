"""
Run both the FastAPI application and Flask test website with production configuration.
"""

import subprocess
import sys
import time
import signal
import os
import argparse

def run_servers(production_mode=False):
    """
    Start both the main FastAPI server and the Flask test website server.
    Handle graceful shutdown on exit.
    
    Args:
        production_mode: If True, run in production mode (disables test redirects)
    """
    print("Starting Email QA Automation servers...")
    
    # Set environment variable for production mode
    env = os.environ.copy()
    if production_mode:
        env["EMAIL_QA_ENV"] = "production"
        print("Running in PRODUCTION mode")
    else:
        env["EMAIL_QA_ENV"] = "development"
        print("Running in DEVELOPMENT mode")
    
    # Start the FastAPI server (main application)
    fastapi_process = subprocess.Popen(
        ["python", "main_prod.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env
    )
    
    # Start the Flask test website
    flask_process = subprocess.Popen(
        ["python", "test_website.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env
    )
    
    print(f"FastAPI server PID: {fastapi_process.pid}")
    print(f"Flask test website PID: {flask_process.pid}")
    
    # Function to handle graceful shutdown
    def signal_handler(sig, frame):
        print("\nShutting down servers...")
        flask_process.terminate()
        fastapi_process.terminate()
        sys.exit(0)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Monitor both processes and relay output
        while True:
            # Check FastAPI output
            if fastapi_process.stdout and not fastapi_process.stdout.closed:
                fastapi_line = fastapi_process.stdout.readline()
                if fastapi_line:
                    print(f"[FastAPI] {fastapi_line.rstrip()}")
            
            # Check Flask output
            if flask_process.stdout and not flask_process.stdout.closed:
                flask_line = flask_process.stdout.readline()
                if flask_line:
                    print(f"[Flask] {flask_line.rstrip()}")
            
            # Check if either process has terminated
            if fastapi_process.poll() is not None:
                print("FastAPI server has stopped. Shutting down...")
                flask_process.terminate()
                break
                
            if flask_process.poll() is not None:
                print("Flask test website has stopped. Shutting down...")
                fastapi_process.terminate()
                break
                
            # Small sleep to prevent high CPU usage
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        flask_process.terminate()
        fastapi_process.terminate()
    
    # Wait for processes to terminate
    fastapi_process.wait()
    flask_process.wait()
    print("All servers stopped.")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Run Email QA Automation servers')
    parser.add_argument(
        '--development', 
        action='store_true',
        help='Run in development mode (enables test redirects)'
    )
    
    args = parser.parse_args()
    # Run in production mode by default
    run_servers(production_mode=not args.development)