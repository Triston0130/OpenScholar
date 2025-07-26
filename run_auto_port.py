#!/usr/bin/env python3
"""
OpenScholar API startup script with automatic port selection
"""
import uvicorn
import socket
import sys

def find_free_port(start_port=8000, max_port=9000):
    """Find a free port starting from start_port"""
    for port in range(start_port, max_port):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('', port))
                return port
        except OSError:
            continue
    return None

if __name__ == "__main__":
    # Try to find a free port
    free_port = find_free_port(8000)
    
    if free_port:
        print(f"🚀 Starting OpenScholar on port {free_port}")
        print(f"📍 Access the API at: http://localhost:{free_port}")
        print(f"📋 Health check: http://localhost:{free_port}/health")
        print(f"📖 API docs: http://localhost:{free_port}/docs")
        
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=free_port,
            reload=True,
            log_level="info"
        )
    else:
        print("❌ No free ports available between 8000-9000")
        sys.exit(1)
