#!/usr/bin/env python3
"""
Debug version of OpenScholar API startup
"""
import sys
import uvicorn
import logging

# Set up logging to see what's happening
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting OpenScholar API in debug mode...")
    
    try:
        logger.info("Importing FastAPI app...")
        from app.main import app
        logger.info("FastAPI app imported successfully")
        
        logger.info("Starting Uvicorn server...")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8001,
            log_level="debug",
            access_log=True
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}", exc_info=True)
        sys.exit(1)