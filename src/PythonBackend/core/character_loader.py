"""
Character Loader for Windows AI Assistant
Handles loading and managing AI character personalities
"""

import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import logging

class CharacterLoader:
    """Load and manage AI character definitions"""
    
    def __init__(self, config_path: str = "../configs"):
        """
        Initialize Character Loader
        
        Args:
            config_path (str): Path to configuration directory
        """
        self.logger = self._setup_logger()
        self.config_path = Path(config_path)
        self.characters_dir = self.config_path / "characters"
        self.characters = {}
        self.default_characters = self._create_default_characters()
        self._ensure_directories_exist()
        self.load_characters()
        self.logger.info("CharacterLoader initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the character loader"""
        logger = logging.getLogger('CharacterLoader')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger
    
    def _ensure_directories_exist(self):
        """Ensure required directories exist"""
        self.characters_dir.mkdir(parents=True, exist_ok=True)
    
    def _create_default_characters(self) -> Dict[str, Any]:
        """Create default character definitions"""
        return {
            "artemis": {
                "id": "artemis",
                "name": {
                    "tr": "Artemis",
                    "en": "Artemis"
                },
                "description": {
                    "tr": "Dost canlısı kişisel asistan",
                    "en": "Friendly personal assistant"
                },
                "personality_traits": {
                    "friendly": 0.8,
                    "professional": 0.3,
                    "humorous": 0.6,
                    "empathetic": 0.7,
                    "curious": 0.5
                },
                "communication_style": {
                    "formality": "casual",
                    "tone": "warm",
                    "response_length": "medium"
                },
                "voice_settings": {
                    "engine": "pyttsx3",
                    "voice_gender": "female",
                    "speaking_rate": 200,
                    "volume": 0.8
                },
                "capabilities": {
                    "weather_queries": True,
                    "time_date": True,
                    "calculator": True,
                    "web_search": True,
                    "file_operations": False,
                    "email": False
                },
                "response_templates": {
                    "greeting": {
                        "tr": "Merhaba! Size nasıl yardımcı olabilirim?",
                        "en": "Hello! How can I help you today?"
                    },
                    "farewell": {
                        "tr": "Görüşmek üzere!",
                        "en": "See you later!"
                    },
                    "help": {
                        "tr": "Size şu konularda yardımcı olabilirim: zaman, hava durumu, temel hesaplamalar",
                        "en": "I can help you with: time, weather, basic calculations"
                    }
                },
                "profile_compatibility": ["personal", "education"]
            },
            "corporate": {
                "id": "corporate",
                "name": {
                    "tr": "Kurumsal Danışman",
                    "en": "Corporate Advisor"
                },
                "description": {
                    "tr": "Profesyonel iş ortamı asistanı",
                    "en": "Professional business environment assistant"
                },
                "personality_traits": {
                    "friendly": 0.5,
                    "professional": 0.9,
                    "humorous": 0.2,
                    "empathetic": 0.6,
                    "curious": 0.4
                },
                "communication_style": {
                    "formality": "formal",
                    "tone": "professional",
                    "response_length": "concise"
                },
                "voice_settings": {
                    "engine": "pyttsx3",
                    "voice_gender": "neutral",
                    "speaking_rate": 180,
                    "volume": 0.7
                },
                "capabilities": {
                    "weather_queries": True,
                    "time_date": True,
                    "calculator": True,
                    "web_search": True,
                    "file_operations": True,
                    "email": True,
                    "calendar_management": True
                },
                "response_templates": {
                    "greeting": {
                        "tr": "Günaydın. Size nasıl yardımcı olabilirim?",
                        "en": "Good morning. How may I assist you?"
                    },
                    "farewell": {
                        "tr": "İyi günler dilerim.",
                        "en": "Have a good day."
                    },
                    "help": {
                        "tr": "Size şu konularda yardımcı olabilirim: toplantı planlama, e-posta yönetimi, dosya işlemleri",
                        "en": "I can assist with: meeting scheduling, email management, file operations"
                    }
                },
                "profile_compatibility": ["business"]
            },
            "study_buddy": {
                "id": "study_buddy",
                "name": {
                    "tr": "Study Buddy",
                    "en": "Study Buddy"
                },
                "description": {
                    "tr": "Öğrenciler için eğitim asistanı",
                    "en": "Educational assistant for students"
                },
                "personality_traits": {
                    "friendly": 0.7,
                    "professional": 0.4,
                    "humorous": 0.8,
                    "empathetic": 0.9,
                    "curious": 0.9
                },
                "communication_style": {
                    "formality": "casual",
                    "tone": "encouraging",
                    "response_length": "detailed"
                },
                "voice_settings": {
                    "engine": "pyttsx3",
                    "voice_gender": "neutral",
                    "speaking_rate": 220,
                    "volume": 0.9
                },
                "capabilities": {
                    "weather_queries": True,
                    "time_date": True,
                    "calculator": True,
                    "web_search": True,
                    "study_tools": True,
                    "quiz_generation": True,
                    "explanation_assistance": True
                },
                "response_templates": {
                    "greeting": {
                        "tr": "Merhaba! Bugün hangi konuyu çalışacağız?",
                        "en": "Hello! What subject shall we study today?"
                    },
                    "farewell": {
                        "tr": "Çalışmalarında başarılar! Görüşürüz!",
                        "en": "Good luck with your studies! See you!"
                    },
                    "help": {
                        "tr": "Size şu konularda yardımcı olabilirim: konu anlatımı, quiz hazırlama, çalışma planı",
                        "en": "I can help with: topic explanation, quiz preparation, study planning"
                    }
                },
                "profile_compatibility": ["education"]
            }
        }
    
    def load_characters(self) -> Dict[str, Any]:
        """
        Load characters from JSON files or use defaults
        
        Returns:
            Dict: Loaded characters dictionary
        """
        try:
            # Önce varsayılan karakterleri yükle
            self.characters = self.default_characters.copy()
            
            # Karakter dizinindeki JSON dosyalarını kontrol et
            if self.characters_dir.exists():
                for character_file in self.characters_dir.glob("*.json"):
                    try:
                        with open(character_file, 'r', encoding='utf-8') as f:
                            character_data = json.load(f)
                            character_id = character_data.get('id', character_file.stem)
                            self.characters[character_id] = character_data
                            self.logger.info(f"Loaded custom character: {character_id}")
                    except Exception as e:
                        self.logger.warning(f"Could not load character {character_file}: {e}")
            
            self.logger.info(f"Loaded {len(self.characters)} characters")
            return self.characters
            
        except Exception as e:
            self.logger.error(f"Error loading characters: {e}")
            # En azından varsayılan karakterleri döndür
            self.characters = self.default_characters
            return self.characters
    
    def load_character(self, character_id: str) -> Optional[Dict[str, Any]]:
        """
        Load specific character by ID
        
        Args:
            character_id (str): Character identifier
            
        Returns:
            Dict or None: Character data or None if not found
        """
        character = self.characters.get(character_id)
        if character:
            self.logger.info(f"Character loaded: {character_id}")
            return character
        else:
            self.logger.warning(f"Character not found: {character_id}")
            return None
    
    def get_character(self, character_id: str) -> Optional[Dict[str, Any]]:
        """
        Get character data (alias for load_character)
        
        Args:
            character_id (str): Character identifier
            
        Returns:
            Dict or None: Character data
        """
        return self.load_character(character_id)
    
    def list_characters(self) -> List[Dict[str, Any]]:
        """
        List all available characters with basic info
        
        Returns:
            List[Dict]: List of character summaries
        """
        character_list = []
        for character_id, character_data in self.characters.items():
            character_list.append({
                "id": character_id,
                "name": character_data.get("name", {}),
                "description": character_data.get("description", {}),
                "profile_compatibility": character_data.get("profile_compatibility", [])
            })
        return character_list
    
    def get_character_names(self) -> List[str]:
        """
        Get list of character IDs
        
        Returns:
            List[str]: List of character identifiers
        """
        return list(self.characters.keys())
    
    def get_compatible_characters(self, profile_id: str) -> List[str]:
        """
        Get characters compatible with specific profile
        
        Args:
            profile_id (str): Profile identifier
            
        Returns:
            List[str]: List of compatible character IDs
        """
        compatible_chars = []
        for char_id, char_data in self.characters.items():
            compatibility_list = char_data.get("profile_compatibility", [])
            if profile_id in compatibility_list or not compatibility_list:
                compatible_chars.append(char_id)
        return compatible_chars
    
    def validate_character_compatibility(self, character_id: str, profile_id: str) -> bool:
        """
        Validate if character is compatible with profile
        
        Args:
            character_id (str): Character identifier
            profile_id (str): Profile identifier
            
        Returns:
            bool: Compatibility status
        """
        character = self.get_character(character_id)
        if not character:
            return False
        
        compatibility_list = character.get("profile_compatibility", [])
        # Boş liste tüm profillerle uyumlu demektir
        if not compatibility_list:
            return True
        
        return profile_id in compatibility_list
    
    def save_character(self, character_id: str, character_data: Dict[str, Any]) -> bool:
        """
        Save character to file (future feature)
        
        Args:
            character_id (str): Character identifier
            character_data (Dict): Character data to save
            
        Returns:
            bool: Success status
        """
        try:
            character_file = self.characters_dir / f"{character_id}.json"
            with open(character_file, 'w', encoding='utf-8') as f:
                json.dump(character_data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"Saved character: {character_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving character {character_id}: {e}")
            return False

# Test function
def test_character_loader():
    """Test Character Loader functionality"""
    print("🎭 Testing Character Loader...")
    
    # Create loader instance
    cl = CharacterLoader()
    
    # Test character listing
    print(f"\n📋 Available characters: {cl.get_character_names()}")
    
    # Test specific character loading
    artemis = cl.load_character("artemis")
    if artemis:
        print(f"\n👤 Artemis: {artemis.get('name', {}).get('tr', 'N/A')}")
        print(f"   Personality: {artemis.get('personality_traits', {})}")
    
    # Test character listing
    char_list = cl.list_characters()
    print(f"\n📝 Character List:")
    for char in char_list:
        print(f"  - {char['id']}: {char['name'].get('tr', 'N/A')}")
    
    # Test compatibility
    compatible_with_personal = cl.get_compatible_characters("personal")
    print(f"\n🤝 Compatible with personal profile: {compatible_with_personal}")
    
    # Test validation
    is_compatible = cl.validate_character_compatibility("artemis", "personal")
    print(f"   Artemis-Personal compatibility: {is_compatible}")
    
    print("\n✅ Character Loader test completed!")

if __name__ == "__main__":
    test_character_loader()
