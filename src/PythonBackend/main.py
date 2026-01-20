#!/usr/bin/env python3
"""
Windows AI Assistant - Python Backend
Complete version with all routes working
"""

import sys
import os
from pathlib import Path

# Python path'i düzenle
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

print(f"Working directory: {current_dir}")
print(f"Python path: {sys.path[:3]}...")

try:
    # FastAPI imports
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    import uvicorn
    
    print("✅ FastAPI components imported")
    
    # Core components
    try:
        from core.ai_engine import AICoreEngine
        HAS_AI_ENGINE = True
        print("✅ AI Engine available")
    except ImportError as e:
        HAS_AI_ENGINE = False
        print(f"⚠️  AI Engine not available: {e}")
    
    # Create app
    app = FastAPI(
        title="Windows AI Assistant",
        version="1.0.0",
        description="AI Core Engine API with Profile and Character Support"
    )
    
    # Pydantic Models
    class TextInput(BaseModel):
        text: str

    class ProfileSwitchRequest(BaseModel):
        profile_id: str
        character_id: str = None

    class CharacterSwitchRequest(BaseModel):
        character_id: str

    # Global AI engine
    ai_engine = None
    if HAS_AI_ENGINE:
        try:
            ai_engine = AICoreEngine()
            ai_engine.initialize("personal", "artemis")  # Default başlat
            print("✅ AI Engine initialized")
        except Exception as e:
            print(f"⚠️  AI Engine init error: {e}")
            ai_engine = None

    # === ROOT ENDPOINTS ===
    @app.get("/")
    async def root():
        return {
            "message": "Windows AI Assistant Backend Running",
            "status": "active",
            "version": "1.0.0"
        }

    @app.get("/health")
    async def health():
        return {"status": "healthy", "service": "AI Assistant Backend"}

    # === AI ENDPOINTS ===
    @app.post("/ai/process")
    async def process_ai(input_data: TextInput):
        if not HAS_AI_ENGINE or ai_engine is None:
            raise HTTPException(status_code=500, detail="AI Engine not available")
        
        try:
            result = ai_engine.process_input(input_data.text)
            return result
        except Exception as e:
            return {"error": str(e), "status": "error"}

    @app.get("/ai/status")
    async def ai_status():
        if not HAS_AI_ENGINE or ai_engine is None:
            return {"status": "AI Engine not available"}
        
        try:
            return ai_engine.get_status()
        except Exception as e:
            return {"status": "error", "error": str(e)}

    @app.get("/ai/profiles")
    async def list_profiles():
        if not HAS_AI_ENGINE or ai_engine is None:
            return {"profiles": [], "error": "AI Engine not available"}
        
        try:
            profiles = ai_engine.get_available_profiles()
            return {"profiles": profiles}
        except Exception as e:
            return {"error": str(e)}

    @app.get("/ai/characters")
    async def list_characters():
        if not HAS_AI_ENGINE or ai_engine is None:
            return {"characters": [], "error": "AI Engine not available"}
        
        try:
            characters = ai_engine.get_available_characters()
            return {"characters": characters}
        except Exception as e:
            return {"error": str(e)}

    @app.post("/ai/profile/switch")
    async def switch_profile(profile_request: ProfileSwitchRequest):
        if not HAS_AI_ENGINE or ai_engine is None:
            raise HTTPException(status_code=500, detail="AI Engine not available")
        
        try:
            success = ai_engine.switch_profile(
                profile_request.profile_id, 
                profile_request.character_id
            )
            return {
                "message": f"Switched to profile: {profile_request.profile_id}" + 
                          (f" with character: {profile_request.character_id}" if profile_request.character_id else ""),
                "success": success
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/ai/character/switch")
    async def switch_character(character_request: CharacterSwitchRequest):
        if not HAS_AI_ENGINE or ai_engine is None:
            raise HTTPException(status_code=500, detail="AI Engine not available")
        
        try:
            current_profile = ai_engine.current_profile.get('id') if ai_engine.current_profile else "personal"
            success = ai_engine.switch_character(character_request.character_id)
            return {
                "message": f"Switched to character: {character_request.character_id}",
                "success": success
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/ai/compatibility/{profile_id}")
    async def get_compatible_characters(profile_id: str):
        if not HAS_AI_ENGINE:
            raise HTTPException(status_code=500, detail="AI Engine not available")
        
        try:
            # Direct character loader access
            from core.character_loader import CharacterLoader
            loader = CharacterLoader()
            compatible = loader.get_compatible_characters(profile_id)
            return {"profile": profile_id, "compatible_characters": compatible}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    print("✅ All API routes registered successfully")
    
except Exception as e:
    print(f"❌ Error during startup: {e}")
    # Fallback app
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/")
    async def fallback():
        return {"message": "Fallback app running", "error": str(e)}

if __name__ == "__main__":
    print("🚀 Starting FastAPI server on http://0.0.0.0:8000")
    print("📄 Docs: http://0.0.0.0:8000/docs")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
