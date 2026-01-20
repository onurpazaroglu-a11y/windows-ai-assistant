"""
AI Routes for FastAPI with Full Integration
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import sys
import os

# Absolute import fix
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(current_dir, '..', '..')
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

try:
    from core.ai_engine import AICoreEngine
    ENGINE_AVAILABLE = True
    print("✅ AI Engine imported successfully")
except ImportError as e:
    print(f"⚠️  Core engine import warning: {e}")
    ENGINE_AVAILABLE = False

# Check for DatabaseManager availability
try:
    from core.database_manager import DatabaseManager
    DATABASE_MANAGER_AVAILABLE = True
except ImportError:
    DATABASE_MANAGER_AVAILABLE = False

# Request models
class TextInput(BaseModel):
    text: str

class ProfileSwitchRequest(BaseModel):
    profile_id: str
    character_id: str = None

class CharacterSwitchRequest(BaseModel):
    character_id: str

class BackupRequest(BaseModel):
    backup_path: Optional[str] = None

# Router
router = APIRouter(prefix="/ai", tags=["AI Engine"])

# AI engine instance
ai_engine = None
if ENGINE_AVAILABLE:
    try:
        ai_engine = AICoreEngine()
        # Default profile ve karakter ile başlat
        ai_engine.initialize("personal", "artemis")
        print("✅ AI Engine instance created")
    except Exception as e:
        print(f"⚠️  AI Engine creation error: {e}")
        ENGINE_AVAILABLE = False

@router.post("/process")
async def process_input(input_data: TextInput):
    """Process user input with current profile and character"""
    if not ENGINE_AVAILABLE or ai_engine is None:
        raise HTTPException(status_code=500, detail="AI Engine not available")
    
    try:
        result = ai_engine.process_input(input_data.text)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_status():
    """Get AI engine status including all components"""
    if not ENGINE_AVAILABLE or ai_engine is None:
        return {"status": "AI Engine not available"}
    
    try:
        status = ai_engine.get_status()
        return status
    except Exception as e:
        return {"status": "error", "error": str(e)}

@router.get("/profiles")
async def list_profiles():
    """List available profiles"""
    if not ENGINE_AVAILABLE or ai_engine is None:
        raise HTTPException(status_code=500, detail="AI Engine not available")
    
    try:
        profiles = ai_engine.get_available_profiles()
        return {"profiles": profiles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/characters")
async def list_characters():
    """List available characters"""
    if not ENGINE_AVAILABLE or ai_engine is None:
        raise HTTPException(status_code=500, detail="AI Engine not available")
    
    try:
        characters = ai_engine.get_available_characters()
        return {"characters": characters}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/profile/switch")
async def switch_profile(profile_request: ProfileSwitchRequest):
    """Switch to different profile (and optionally character)"""
    if not ENGINE_AVAILABLE or ai_engine is None:
        raise HTTPException(status_code=500, detail="AI Engine not available")
    
    try:
        success = ai_engine.switch_profile(
            profile_request.profile_id, 
            profile_request.character_id
        )
        if success:
            return {
                "message": f"Switched to profile: {profile_request.profile_id}" + 
                          (f" with character: {profile_request.character_id}" if profile_request.character_id else ""),
                "success": True
            }
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to switch to profile: {profile_request.profile_id}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/character/switch")
async def switch_character(character_request: CharacterSwitchRequest):
    """Switch to different character"""
    if not ENGINE_AVAILABLE or ai_engine is None:
        raise HTTPException(status_code=500, detail="AI Engine not available")
    
    try:
        success = ai_engine.switch_character(character_request.character_id)
        if success:
            return {
                "message": f"Switched to character: {character_request.character_id}",
                "success": True
            }
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to switch to character: {character_request.character_id}"
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compatibility/{profile_id}")
async def get_compatible_characters(profile_id: str):
    """Get characters compatible with specific profile"""
    if not ENGINE_AVAILABLE:
        raise HTTPException(status_code=500, detail="AI Engine not available")
    
    try:
        # Try to access character loader directly
        from core.character_loader import CharacterLoader
        loader = CharacterLoader()
        compatible = loader.get_compatible_characters(profile_id)
        return {"profile": profile_id, "compatible_characters": compatible}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Database-related endpoints (only if DatabaseManager is available)
if DATABASE_MANAGER_AVAILABLE:
    @router.post("/database/backup")
    async def backup_database(backup_request: BackupRequest = None):
        """Backup database"""
        if not ENGINE_AVAILABLE or ai_engine is None or ai_engine.database_manager is None:
            raise HTTPException(status_code=500, detail="Database Manager not available")
        
        try:
            backup_path = backup_request.backup_path if backup_request else None
            success = ai_engine.database_manager.backup_database(backup_path)
            return {
                "success": success, 
                "message": "Database backup completed" if success else "Backup failed",
                "backup_path": backup_path or "default_location"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/database/stats")
    async def get_database_stats():
        """Get database statistics"""
        if not ENGINE_AVAILABLE or ai_engine is None or ai_engine.database_manager is None:
            raise HTTPException(status_code=500, detail="Database Manager not available")
        
        try:
            stats = ai_engine.database_manager.get_database_stats()
            return stats
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/database/metrics")
    async def get_database_metrics(category: str = None, hours: int = 24):
        """Get database metrics"""
        if not ENGINE_AVAILABLE or ai_engine is None or ai_engine.database_manager is None:
            raise HTTPException(status_code=500, detail="Database Manager not available")
        
        try:
            metrics = ai_engine.database_manager.get_metrics_summary(category, hours)
            return metrics
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/database/cleanup")
    async def cleanup_database(days_to_keep: int = 30):
        """Clean up old database records"""
        if not ENGINE_AVAILABLE or ai_engine is None or ai_engine.database_manager is None:
            raise HTTPException(status_code=500, detail="Database Manager not available")
        
        try:
            results = ai_engine.database_manager.cleanup_old_data(days_to_keep)
            return {
                "success": True,
                "cleanup_results": results,
                "message": f"Cleaned up data older than {days_to_keep} days"
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.get("/test")
async def test_route():
    """Test endpoint"""
    return {"message": "AI Routes working!"}

# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint"""
    if ENGINE_AVAILABLE and ai_engine and ai_engine.is_initialized:
        return {
            "status": "healthy",
            "engine": "running",
            "components": {
                "profile_manager": ai_engine.profile_manager is not None,
                "character_loader": ai_engine.character_loader is not None,
                "context_manager": ai_engine.context_manager is not None,
                "response_generator": ai_engine.response_generator is not None,
                "database_manager": ai_engine.database_manager is not None if hasattr(ai_engine, 'database_manager') else False
            }
        }
    else:
        return {
            "status": "degraded",
            "engine": "not_initialized",
            "message": "AI Engine components may be missing"
        }
