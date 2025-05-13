import subprocess
import sys
import time
import signal
import os
import argparse
from runtime_config import config

def run_servers(initial_mode=None):
    """
    Start both the main FastAPI server and the Flask test website server.
    Handle graceful shutdown on exit.
    
    Args:
        initial_mode: Override the initial application mode (development/production)
    """
    # Set initial mode if specified
    if initial_mode:
        config.set_mode(initial_mode)
        print(f"Starting Email QA Automation in {config.mode.upper()} mode...")
    else:
        print(f"Starting Email QA Automation in {config.mode.upper()} mode (default)...")
    
    # Set environment variable for configuration
    env = os.environ.copy()
    env["EMAIL_QA_MODE"] = config.mode
    
    # Determine if this is a deployment environment
    is_deployment = os.environ.get("REPL_SLUG") is not None and os.environ.get("REPL_OWNER") is not None
    
    # Start the FastAPI server (main application) on port 5000
    # Use a consistent import path regardless of environment
    server_cmd = ["python", "-c", 
                 "import uvicorn; import simple_mode_switcher; "
                 "print('Running in DEPLOYMENT mode' if {} else 'Running in local mode'); "
                 "uvicorn.run(simple_mode_switcher.app, host='0.0.0.0', port=5000)".format(is_deployment)]
    
    fastapi_process = subprocess.Popen(
        server_cmd,
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
        '--mode', 
        choices=['development', 'production'],
        help='Set initial application mode'
    )
    
    args = parser.parse_args()
    run_servers(initial_mode=args.mode)