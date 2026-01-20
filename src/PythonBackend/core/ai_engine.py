"""
Enhanced AI Core Engine with Database Integration
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
import sys
import os
import time

# Component imports
try:
    from .profile_manager import ProfileManager
    PROFILE_MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"Profile Manager not available: {e}")
    PROFILE_MANAGER_AVAILABLE = False

try:
    from .character_loader import CharacterLoader
    CHARACTER_LOADER_AVAILABLE = True
except ImportError as e:
    print(f"Character Loader not available: {e}")
    CHARACTER_LOADER_AVAILABLE = False

try:
    from .context_manager import ContextManager
    CONTEXT_MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"Context Manager not available: {e}")
    CONTEXT_MANAGER_AVAILABLE = False

try:
    from .response_generator import ResponseGenerator
    RESPONSE_GENERATOR_AVAILABLE = True
except ImportError as e:
    print(f"Response Generator not available: {e}")
    RESPONSE_GENERATOR_AVAILABLE = False

try:
    from .database_manager import DatabaseManager
    DATABASE_MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"Database Manager not available: {e}")
    DATABASE_MANAGER_AVAILABLE = False

class AICoreEngine:
    """Enhanced AI Engine with Database Integration"""
    
    def __init__(self, session_id: str = "default_session"):
        self.setup_logging()
        self.logger.info("AICoreEngine initializing...")
        self.session_id = session_id
        
        # Initialize timing
        self.start_time = time.time()
        
        # Profile manager
        if PROFILE_MANAGER_AVAILABLE:
            try:
                self.profile_manager = ProfileManager()
                self.logger.info("✅ Profile Manager loaded")
            except Exception as e:
                self.logger.error(f"Profile Manager init error: {e}")
                self.profile_manager = None
        else:
            self.profile_manager = None
            self.logger.warning("⚠️  Profile Manager not available")
        
        # Character loader
        if CHARACTER_LOADER_AVAILABLE:
            try:
                self.character_loader = CharacterLoader()
                self.logger.info("✅ Character Loader loaded")
            except Exception as e:
                self.logger.error(f"Character Loader init error: {e}")
                self.character_loader = None
        else:
            self.character_loader = None
            self.logger.warning("⚠️  Character Loader not available")
        
        # Context manager
        if CONTEXT_MANAGER_AVAILABLE:
            try:
                self.context_manager = ContextManager()
                self.logger.info("✅ Context Manager loaded")
            except Exception as e:
                self.logger.error(f"Context Manager init error: {e}")
                self.context_manager = None
        else:
            self.context_manager = None
            self.logger.warning("⚠️  Context Manager not available")
        
        # Response generator
        if RESPONSE_GENERATOR_AVAILABLE:
            try:
                self.response_generator = ResponseGenerator()
                self.logger.info("✅ Response Generator loaded")
            except Exception as e:
                self.logger.error(f"Response Generator init error: {e}")
                self.response_generator = None
        else:
            self.response_generator = None
            self.logger.warning("⚠️  Response Generator not available")
        
        # Database manager
        if DATABASE_MANAGER_AVAILABLE:
            try:
                self.database_manager = DatabaseManager()
                self.logger.info("✅ Database Manager loaded")
            except Exception as e:
                self.logger.error(f"Database Manager init error: {e}")
                self.database_manager = None
        else:
            self.database_manager = None
            self.logger.warning("⚠️  Database Manager not available")
        
        self.current_profile = None
        self.current_character = None
        self.is_initialized = False
        self.processing_stats = {
            "total_requests": 0,
            "total_processing_time": 0,
            "average_response_time": 0
        }
        
        # Record initialization time
        init_duration = time.time() - self.start_time
        self._record_metric("initialization_time_ms", init_duration * 1000, "startup")
        
        self.logger.info("AICoreEngine initialized")
    
    def setup_logging(self):
        """Setup logging"""
        self.logger = logging.getLogger('AICoreEngine')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def initialize(self, profile_id: str = "personal", character_id: str = "artemis") -> bool:
        """
        Initialize AI engine with specific profile and character
        
        Args:
            profile_id (str): Profile identifier to load
            character_id (str): Character identifier to load
            
        Returns:
            bool: Initialization success
        """
        init_start = time.time()
        
        try:
            # Load profile
            if self.profile_manager:
                profile = self.profile_manager.get_profile(profile_id)
                if profile:
                    self.current_profile = profile
                    self.logger.info(f"✅ Profile loaded: {profile_id}")
                else:
                    self.logger.error(f"❌ Profile not found: {profile_id}")
                    return False
            else:
                # Fallback
                self.current_profile = {"id": profile_id, "name": profile_id}
                self.logger.info(f"⚠️  Using fallback profile: {profile_id}")
            
            # Load character
            if self.character_loader:
                character = self.character_loader.load_character(character_id)
                if character:
                    # Compatibility check
                    if self.profile_manager:
                        is_compatible = self.character_loader.validate_character_compatibility(
                            character_id, profile_id
                        )
                        if not is_compatible:
                            self.logger.warning(
                                f"⚠️  Character {character_id} may not be compatible with profile {profile_id}"
                            )
                    
                    self.current_character = character
                    self.logger.info(f"✅ Character loaded: {character_id}")
                else:
                    self.logger.error(f"❌ Character not found: {character_id}")
                    return False
            else:
                # Fallback
                self.current_character = {"id": character_id, "name": character_id}
                self.logger.info(f"⚠️  Using fallback character: {character_id}")
            
            self.is_initialized = True
            
            # Record initialization metrics
            init_duration = time.time() - init_start
            self._record_metric("profile_load_time_ms", init_duration * 1000, "initialization")
            
            self.logger.info(f"✅ Engine initialized with profile '{profile_id}' and character '{character_id}'")
            return True
                
        except Exception as e:
            self.logger.error(f"Initialization error: {e}")
            return False
    
    def process_input(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input and return response with full database integration
        
        Args:
            user_input (str): User input text
            
        Returns:
            Dict: Response with text, confidence and metadata
        """
        process_start = time.time()
        self.processing_stats["total_requests"] += 1
        
        try:
            # Get profile and character info
            profile_name = "Unknown"
            character_name = "Unknown"
            profile_id = "unknown"
            character_id = "unknown"
            
            if self.current_profile:
                profile_info = self.current_profile.get('name', {})
                profile_name = profile_info.get('tr', profile_info) if isinstance(profile_info, dict) else str(profile_info)
                profile_id = self.current_profile.get('id', 'unknown')
            
            if self.current_character:
                character_info = self.current_character.get('name', {})
                character_name = character_info.get('tr', character_info) if isinstance(character_info, dict) else str(character_info)
                character_id = self.current_character.get('id', 'unknown')
            
            self.logger.info(f"Processing input - Profile: '{profile_name}', Character: '{character_name}' - Input: {user_input}")
            
            # Get context
            context = []
            if self.context_manager:
                context = self.context_manager.get_context(self.session_id, user_input)
                self.logger.debug(f"Retrieved {len(context)} context items")
            
            # Analyze intent
            intent_analysis_start = time.time()
            intent_analysis = self._analyze_intent(user_input)
            intent_duration = time.time() - intent_analysis_start
            self._record_metric("intent_analysis_time_ms", intent_duration * 1000, "processing")
            self.logger.debug(f"Intent analysis: {intent_analysis}")
            
            # Generate response using ResponseGenerator
            response_generation_start = time.time()
            response_data = None
            if self.response_generator:
                response_data = self.response_generator.generate_response(
                    user_input=user_input,
                    intent=intent_analysis,
                    context=context,
                    character=self.current_character,
                    profile=self.current_profile
                )
                self.logger.debug(f"Generated response with type: {response_data.get('type', 'unknown')}")
            else:
                # Fallback to simple response generation
                response_text = self._generate_simple_response(user_input, context)
                response_data = {
                    "text": response_text,
                    "confidence": 0.7,
                    "type": "simple_fallback"
                }
            
            response_generation_duration = time.time() - response_generation_start
            self._record_metric("response_generation_time_ms", response_generation_duration * 1000, "processing")
            
            # Store interaction in context manager with metrics
            storage_start = time.time()
            if self.context_manager and response_data:
                processing_time_ms = int((time.time() - process_start) * 1000)
                self.context_manager.store_interaction(
                    session_id=self.session_id,
                    user_input=user_input,
                    ai_response=response_data["text"],
                    intent=intent_analysis,
                    profile_id=profile_id,
                    character_id=character_id,
                    processing_time_ms=processing_time_ms
                )
                self.logger.debug("Stored interaction in context manager")
            
            storage_duration = time.time() - storage_start
            self._record_metric("storage_time_ms", storage_duration * 1000, "processing")
            
            # Calculate total processing time
            total_processing_time = time.time() - process_start
            self.processing_stats["total_processing_time"] += total_processing_time
            self.processing_stats["average_response_time"] = (
                self.processing_stats["total_processing_time"] / self.processing_stats["total_requests"]
            )
            
            # Record performance metrics
            self._record_metric("total_processing_time_ms", total_processing_time * 1000, "performance")
            self._record_metric("response_confidence", response_data["confidence"], "quality")
            
            return {
                "response": response_data["text"],
                "confidence": response_data["confidence"],
                "response_type": response_data["type"],
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "profile": profile_id,
                "character": character_id,
                "context_items": len(context) if context else 0,
                "processing_time_ms": int(total_processing_time * 1000),
                "metrics": {
                    "intent_analysis_time_ms": int(intent_duration * 1000),
                    "response_generation_time_ms": int(response_generation_duration * 1000),
                    "storage_time_ms": int(storage_duration * 1000)
                }
            }
        except Exception as e:
            self.logger.error(f"Error: {str(e)}")
            
            # Record error metrics
            error_duration = time.time() - process_start
            self._record_metric("error_processing_time_ms", error_duration * 1000, "errors")
            
            return {
                "response": "Bir hata oluştu",
                "confidence": 0.0,
                "response_type": "error",
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": str(e),
                "processing_time_ms": int(error_duration * 1000)
            }
    
    def _record_metric(self, metric_name: str, metric_value: float, category: str = "general"):
        """
        Record system metrics using DatabaseManager
        
        Args:
            metric_name (str): Metric name
            metric_value (float): Metric value
            category (str): Metric category
        """
        if self.database_manager:
            try:
                self.database_manager.store_metric(metric_name, metric_value, category, self.session_id)
            except Exception as e:
                self.logger.debug(f"Metric recording failed: {e}")
    
    def _analyze_intent(self, text: str) -> Dict[str, Any]:
        """Enhanced intent analysis"""
        text_lower = text.lower()
        
        intents = {
            "greeting": ["merhaba", "selam", "hello", "hi", "günaydın", "iyi akşamlar", "merhabalar"],
            "farewell": ["hoşça kal", "görüşürüz", "bye", "goodbye", "kendine iyi bak", "görüşmek dileğiyle"],
            "question": ["ne", "nasıl", "neden", "kim", "nerede", "hangi", "?", "mı", "mi", "mıdır", "midir", "nedir"],
            "command": ["aç", "kapat", "başlat", "dur", "yap", "oluştur", "sil", "temizle", "ayarla"],
            "time_query": ["saat", "zaman", "tarih", "gün", "time", "date", "now", "bugün", "yarın", "dün", "salı", "çarşamba"],
            "help": ["yardım", "help", "destek", "support", "yardımcı", "ne yapabilirim", "nasıl kullanılır"],
            "personal_info": ["adım", "ismim", "name", "my name", "benim adım", "ismin ne", "adın ne"],
            "wellbeing": ["naber", "nasılsın", "ne haber", "how are you", "iyi misin", "durumun nasıl"],
            "reminder": ["hatırlat", "anımsat", "bilgilendir", "bildir", "alarm", "timer", "remember"],
            "calculation": ["hesapla", "topla", "çıkar", "çarp", "böl", "calculate", "plus", "minus", "times", "divide"],
            "search": ["ara", "bul", "arama", "search", "lookup", "find", "google"]
        }
        
        detected_intents = []
        confidence_scores = {}
        
        for intent_type, keywords in intents.items():
            matches = [keyword for keyword in keywords if keyword in text_lower]
            if matches:
                detected_intents.append(intent_type)
                confidence_scores[intent_type] = min(len(matches) / len(keywords), 1.0)
        
        primary_intent = None
        if confidence_scores:
            primary_intent = max(confidence_scores, key=confidence_scores.get)
        
        return {
            "primary": primary_intent,
            "all_detected": detected_intents,
            "confidence_scores": confidence_scores,
            "text_length": len(text),
            "word_count": len(text.split()),
            "has_question_mark": "?" in text
        }
    
    def _generate_simple_response(self, text: str, context: list) -> str:
        """Simple fallback response generation"""
        text_lower = text.lower()
        
        # Check for personal information in context
        user_name = None
        if self.context_manager:
            user_name = self.context_manager.get_user_fact(self.session_id, "name")
        
        # Character-based responses
        if self.current_character and self.current_character.get('id') == 'corporate':
            if any(word in text_lower for word in ["merhaba", "hello", "hi", "günaydın"]):
                greeting = "Good morning. How may I assist you today?"
                if user_name:
                    greeting = f"Good morning {user_name}. How may I assist you today?"
                return greeting
            elif any(word in text_lower for word in ["meeting", "appointment", "schedule", "toplantı"]):
                return "I can help schedule meetings. Please provide the date and time."
        else:
            if any(word in text_lower for word in ["merhaba", "hello", "hi", "selam", "günaydın"]):
                greeting = "Merhaba! Size nasıl yardımcı olabilirim?"
                if user_name:
                    greeting = f"Merhaba {user_name}! Size nasıl yardımcı olabilirim?"
                return greeting
            elif any(word in text_lower for word in ["saat", "time", "now", "zaman"]):
                return f"Şu anda saat: {datetime.now().strftime('%H:%M:%S')}"
            elif any(word in text_lower for word in ["yardım", "help", "destek"]):
                return "Yardım için şu komutları deneyebilirsiniz: merhaba, saat, yardım"
        
        # Context-aware responses
        if context:
            if any(word in text_lower for word in ["adım neydi", "what was my name", "hatırlıyor musun"]):
                if user_name:
                    return f"Adınız {user_name} olarak hatırlıyorum."
                else:
                    return "Daha önce adınızı söylemediğinizi hatırlıyorum."
        
        # Default fallback
        return "Anlayamadım. 'yardım' yazarak neler yapabileceğimi öğrenin."
    
    def get_available_profiles(self) -> list:
        """Get list of available profiles"""
        if self.profile_manager:
            return self.profile_manager.get_profile_names()
        return ["personal", "business", "education"]  # Fallback
    
    def get_available_characters(self) -> list:
        """Get list of available characters"""
        if self.character_loader:
            return self.character_loader.get_character_names()
        return ["artemis", "corporate", "study_buddy"]  # Fallback
    
    def switch_profile(self, profile_id: str, character_id: str = None) -> bool:
        """Switch to different profile"""
        switch_start = time.time()
        
        if character_id is None:
            # If no character specified, use compatible one or default
            if self.character_loader:
                compatible_chars = self.character_loader.get_compatible_characters(profile_id)
                if compatible_chars:
                    character_id = compatible_chars[0]  # First compatible character
                else:
                    character_id = "artemis"  # Default fallback
            else:
                character_id = "artemis"
        
        result = self.initialize(profile_id, character_id)
        
        # Record switch metrics
        switch_duration = time.time() - switch_start
        self._record_metric("profile_switch_time_ms", switch_duration * 1000, "operations")
        
        return result
    
    def switch_character(self, character_id: str) -> bool:
        """Switch to different character (keep current profile)"""
        switch_start = time.time()
        current_profile_id = self.current_profile.get('id') if self.current_profile else "personal"
        result = self.initialize(current_profile_id, character_id)
        
        # Record switch metrics
        switch_duration = time.time() - switch_start
        self._record_metric("character_switch_time_ms", switch_duration * 1000, "operations")
        
        return result
    
    def get_status(self) -> Dict[str, Any]:
        """Get engine status including all components and database stats"""
        status = {
            "ready": self.is_initialized,
            "current_profile": self.current_profile.get('id') if self.current_profile else None,
            "current_character": self.current_character.get('id') if self.current_character else None,
            "available_profiles": self.get_available_profiles(),
            "available_characters": self.get_available_characters(),
            "session_id": self.session_id,
            "version": "1.0.0",
            "uptime_seconds": time.time() - self.start_time,
            "processing_stats": self.processing_stats
        }
        
        # Add component statuses
        status["components"] = {
            "profile_manager": "active" if self.profile_manager else "inactive",
            "character_loader": "active" if self.character_loader else "inactive",
            "context_manager": "active" if self.context_manager else "inactive",
            "response_generator": "active" if self.response_generator else "inactive",
            "database_manager": "active" if self.database_manager else "inactive"
        }
        
        # Add context stats if available
        if self.context_manager:
            try:
                context_stats = self.context_manager.get_context_stats()
                status["context_stats"] = context_stats
            except Exception as e:
                self.logger.debug(f"Could not get context stats: {e}")
        
        # Add response generator stats if available
        if self.response_generator:
            try:
                response_stats = self.response_generator.get_response_statistics()
                status["response_stats"] = response_stats
            except Exception as e:
                self.logger.debug(f"Could not get response stats: {e}")
        
        # Add database stats if available
        if self.database_manager:
            try:
                db_stats = self.database_manager.get_database_stats()
                status["database_stats"] = db_stats
                
                # Add performance metrics
                metrics_summary = self.database_manager.get_metrics_summary(hours_back=1)
                status["performance_metrics"] = metrics_summary
            except Exception as e:
                self.logger.debug(f"Could not get database stats: {e}")
        
        return status

# Test
if __name__ == "__main__":
    engine = AICoreEngine()
    engine.initialize("personal", "artemis")
    result = engine.process_input("Merhaba")
    print("Test result:", result)
