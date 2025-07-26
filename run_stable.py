#!/usr/bin/env python3
"""
Stable OpenScholar API runner with auto-restart
"""
import subprocess
import time
import sys
import os

def run_backend():
    """Run the backend with automatic restart on failure"""
    while True:
        print(f"\n{'='*50}")
        print("Starting OpenScholar backend on port 8000...")
        print(f"{'='*50}\n")
        
        try:
            # Activate virtual environment and run the backend
            process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "app.main:app", 
                 "--host", "0.0.0.0", 
                 "--port", "8000",
                 "--reload",
                 "--log-level", "info"],
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            
            # Wait for the process to complete
            process.wait()
            
        except KeyboardInterrupt:
            print("\n\nShutting down gracefully...")
            if process:
                process.terminate()
            break
        except Exception as e:
            print(f"\nError occurred: {e}")
            print("Restarting in 5 seconds...")
            time.sleep(5)
        
        print("\nBackend stopped unexpectedly. Restarting in 3 seconds...")
        time.sleep(3)

if __name__ == "__main__":
    run_backend()