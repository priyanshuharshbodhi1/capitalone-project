#!/usr/bin/env python3
"""
Main entry point for the FastAPI application.
This file is used by Render to start the server.
"""

import uvicorn
from server.api.main import app

if __name__ == "__main__":
    # Get port from environment variable (Render provides this)
    import os
    port = int(os.environ.get("PORT", 8000))
    
    # Run the FastAPI app
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
