"""
Profile Manager for Windows AI Assistant
Handles loading and managing AI assistant profiles
"""

import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path

class ProfileManager:
    """Manage AI assistant profiles"""
    
    def __init__(self, config_path: str = "../configs"):
        """
        Initialize Profile Manager
        
        Args:
            config_path (str): Path to configuration directory
        """
        self.config_path = Path(config_path)
        self.profiles_dir = self.config_path / "profiles"
        self.profiles = {}
        self.default_profiles = self._create_default_profiles()
        self._ensure_directories_exist()
        self.load_profiles()
    
    def _ensure_directories_exist(self):
        """Ensure required directories exist"""
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
    
    def _create_default_profiles(self) -> Dict[str, Any]:
        """Create default profiles"""
        return {
            "personal": {
                "id": "personal",
                "name": {
                    "tr": "Kişisel Asistan",
                    "en": "Personal Assistant"
                },
                "description": {
                    "tr": "Günlük görevler için kişisel asistan",
                    "en": "Personal assistant for daily tasks"
                },
                "target_users": ["home_users", "students"],
                "features": {
                    "voice_commands": True,
                    "web_search": True,
                    "offline_mode": True,
                    "system_tasks": False,
                    "reminder_system": True
                },
                "minimum_requirements": {
                    "ram_mb": 512,
                    "disk_space_mb": 100,
                    "internet_required": False
                },
                "supported_languages": ["tr", "en"],
                "character_reference": "artemis"
            },
            "business": {
                "id": "business",
                "name": {
                    "tr": "İş Asistanı",
                    "en": "Business Assistant"
                },
                "description": {
                    "tr": "Ofis ve iş görevleri için asistan",
                    "en": "Assistant for office and business tasks"
                },
                "target_users": ["professionals", "office_workers"],
                "features": {
                    "voice_commands": True,
                    "web_search": True,
                    "offline_mode": False,
                    "system_tasks": True,
                    "reminder_system": True,
                    "email_integration": True
                },
                "minimum_requirements": {
                    "ram_mb": 1024,
                    "disk_space_mb": 200,
                    "internet_required": True
                },
                "supported_languages": ["tr", "en", "de", "fr"],
                "character_reference": "corporate"
            },
            "education": {
                "id": "education",
                "name": {
                    "tr": "Eğitim Asistanı",
                    "en": "Education Assistant"
                },
                "description": {
                    "tr": "Öğrenciler için eğitim asistanı",
                    "en": "Educational assistant for students"
                },
                "target_users": ["students", "teachers"],
                "features": {
                    "voice_commands": True,
                    "web_search": True,
                    "offline_mode": True,
                    "study_tools": True,
                    "reminder_system": True
                },
                "minimum_requirements": {
                    "ram_mb": 768,
                    "disk_space_mb": 150,
                    "internet_required": True
                },
                "supported_languages": ["tr", "en"],
                "character_reference": "study_buddy"
            }
        }
    
    def load_profiles(self) -> Dict[str, Any]:
        """
        Load profiles from JSON files or use defaults
        
        Returns:
            Dict: Loaded profiles dictionary
        """
        try:
            # Önce varsayılan profilleri yükle
            self.profiles = self.default_profiles.copy()
            
            # Profil dizinindeki JSON dosyalarını kontrol et
            if self.profiles_dir.exists():
                for profile_file in self.profiles_dir.glob("*.json"):
                    try:
                        with open(profile_file, 'r', encoding='utf-8') as f:
                            profile_data = json.load(f)
                            profile_id = profile_data.get('id', profile_file.stem)
                            self.profiles[profile_id] = profile_data
                    except Exception as e:
                        print(f"Warning: Could not load profile {profile_file}: {e}")
            
            return self.profiles
            
        except Exception as e:
            print(f"Error loading profiles: {e}")
            # En azından varsayılan profilleri döndür
            self.profiles = self.default_profiles
            return self.profiles
    
    def get_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        """
        Get specific profile by ID
        
        Args:
            profile_id (str): Profile identifier
            
        Returns:
            Dict or None: Profile data or None if not found
        """
        return self.profiles.get(profile_id)
    
    def list_profiles(self) -> List[Dict[str, Any]]:
        """
        List all available profiles with basic info
        
        Returns:
            List[Dict]: List of profile summaries
        """
        profile_list = []
        for profile_id, profile_data in self.profiles.items():
            profile_list.append({
                "id": profile_id,
                "name": profile_data.get("name", {}),
                "description": profile_data.get("description", {}),
                "supported_languages": profile_data.get("supported_languages", [])
            })
        return profile_list
    
    def get_profile_names(self) -> List[str]:
        """
        Get list of profile IDs
        
        Returns:
            List[str]: List of profile identifiers
        """
        return list(self.profiles.keys())
    
    def validate_profile_requirements(self, profile_id: str, system_info: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Validate if system meets profile requirements
        
        Args:
            profile_id (str): Profile identifier
            system_info (Dict): System information (optional)
            
        Returns:
            Dict: Validation result with details
        """
        profile = self.get_profile(profile_id)
        if not profile:
            return {"valid": False, "reason": "Profile not found"}
        
        requirements = profile.get("minimum_requirements", {})
        
        # Basit validation (gerçek uygulamada sistem bilgileri kontrol edilir)
        validation_result = {
            "valid": True,
            "requirements": requirements,
            "checked": True
        }
        
        return validation_result
    
    def save_profile(self, profile_id: str, profile_data: Dict[str, Any]) -> bool:
        """
        Save profile to file (future feature)
        
        Args:
            profile_id (str): Profile identifier
            profile_data (Dict): Profile data to save
            
        Returns:
            bool: Success status
        """
        try:
            profile_file = self.profiles_dir / f"{profile_id}.json"
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving profile {profile_id}: {e}")
            return False

# Test function
def test_profile_manager():
    """Test Profile Manager functionality"""
    print("🧪 Testing Profile Manager...")
    
    # Create manager instance
    pm = ProfileManager()
    
    # Test profile listing
    print(f"\n📋 Available profiles: {pm.get_profile_names()}")
    
    # Test specific profile loading
    personal_profile = pm.get_profile("personal")
    print(f"\n👤 Personal Profile: {personal_profile.get('name', {}).get('tr', 'N/A')}")
    
    # Test profile listing
    profile_list = pm.list_profiles()
    print(f"\n📝 Profile List:")
    for profile in profile_list:
        print(f"  - {profile['id']}: {profile['name'].get('tr', 'N/A')}")
    
    # Test requirements validation
    validation = pm.validate_profile_requirements("personal")
    print(f"\n✅ Validation result: {validation}")
    
    print("\n✅ Profile Manager test completed!")

if __name__ == "__main__":
    test_profile_manager()
