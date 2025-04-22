import subprocess
import sys
import time
import signal
import os

def run_servers():
    """
    Start both the main FastAPI server and the Flask test website server.
    Handle graceful shutdown on exit.
    """
    print("Starting Email QA Automation servers...")
    
    # Start the FastAPI server (main application)
    fastapi_process = subprocess.Popen(
        ["python", "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    # Start the Flask test website
    flask_process = subprocess.Popen(
        ["python", "test_website.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
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
    run_servers()