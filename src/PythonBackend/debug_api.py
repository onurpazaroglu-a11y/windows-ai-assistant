#!/usr/bin/env python3
"""
Debug API routes and structure
"""

import sys
import os
from pathlib import Path

# Add path
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Debug API")

@app.get("/")
async def root():
    return {"message": "Debug API Running"}

@app.get("/test")
async def test():
    return {"message": "Test endpoint working"}

@app.get("/debug/routes")
async def debug_routes():
    """Show all registered routes"""
    routes = []
    for route in app.routes:
        routes.append({
            "path": route.path,
            "methods": list(route.methods),
            "name": route.name
        })
    return {"routes": routes, "count": len(routes)}

# Add some test routes
@app.get("/ai/test")
async def ai_test():
    return {"message": "AI test route working"}

@app.post("/ai/test")
async def ai_test_post():
    return {"message": "AI test POST route working"}

if __name__ == "__main__":
    print("🔍 Debug API starting...")
    print("Routes will be available at http://0.0.0.0:8002")
    uvicorn.run("debug_api:app", host="0.0.0.0", port=8002, reload=True)
