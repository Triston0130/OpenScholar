#!/usr/bin/env python3
"""
OpenScholar API startup script - Fixed version
"""
import uvicorn
import sys

if __name__ == "__main__":
    print("Starting OpenScholar API on port 8001...")
    sys.stdout.flush()
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=False,  # Disable reload to avoid hanging
        log_level="info",
        access_log=True
    )