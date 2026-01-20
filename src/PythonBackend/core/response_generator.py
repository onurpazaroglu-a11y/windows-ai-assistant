"""
Response Generator for Windows AI Assistant
Generates context-aware, character-specific responses
"""

import json
import random
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

class ResponseGenerator:
    """Generate intelligent responses based on context, character, and intent"""
    
    def __init__(self):
        """
        Initialize Response Generator
        """
        self.logger = self._setup_logger()
        self.template_cache = {}
        self.dynamic_variables = {}
        self._initialize_dynamic_variables()
        self.logger.info("ResponseGenerator initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the response generator"""
        logger = logging.getLogger('ResponseGenerator')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger
    
    def _initialize_dynamic_variables(self):
        """Initialize dynamic variables that can be used in templates"""
        self.dynamic_variables = {
            'time': lambda: datetime.now().strftime('%H:%M'),
            'date': lambda: datetime.now().strftime('%d.%m.%Y'),
            'day_of_week': lambda: datetime.now().strftime('%A'),
            'greeting_time': self._get_time_based_greeting,
            'random_positive': lambda: random.choice(['harika', 'mükemmel', 'güzel', 'iyi']),
            'random_negative': lambda: random.choice(['üzgünüm', 'maalesef', 'ne yazık ki'])
        }
    
    def _get_time_based_greeting(self) -> str:
        """Get time-based greeting"""
        hour = datetime.now().hour
        if 5 <= hour < 12:
            return "Günaydın"
        elif 12 <= hour < 18:
            return "İyi günler"
        else:
            return "İyi akşamlar"
    
    def generate_response(self, user_input: str, intent: Dict[str, Any], 
                         context: List[Dict[str, Any]], character: Dict[str, Any] = None,
                         profile: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate response based on input, intent, context, character and profile
        
        Args:
            user_input (str): User's input text
            intent (Dict): Intent analysis results
            context (List): Conversation context
            character (Dict): Character definition
            profile (Dict): Profile definition
            
        Returns:
            Dict: Response with text, confidence and metadata
        """
        try:
            # Extract relevant information
            primary_intent = intent.get('primary', 'unknown')
            confidence_scores = intent.get('confidence_scores', {})
            user_input_lower = user_input.lower()
            
            self.logger.debug(f"Generating response for intent: {primary_intent}")
            
            # Try character-specific response first
            response = self._generate_character_response(
                user_input, primary_intent, context, character
            )
            
            if response:
                return response
            
            # Try intent-based response
            response = self._generate_intent_response(
                user_input, primary_intent, context
            )
            
            if response:
                return response
            
            # Fallback to template-based response
            response = self._generate_template_response(
                user_input, primary_intent, context, character
            )
            
            return response or self._generate_fallback_response(user_input)
            
        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return self._generate_error_response(str(e))
    
    def _generate_character_response(self, user_input: str, intent: str, 
                                   context: List[Dict], character: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate character-specific response
        
        Args:
            user_input (str): User input
            intent (str): Primary intent
            context (List): Conversation context
            character (Dict): Character definition
            
        Returns:
            Dict or None: Character-specific response
        """
        if not character:
            return None
        
        try:
            character_id = character.get('id', '')
            templates = character.get('response_templates', {})
            personality = character.get('personality_traits', {})
            communication_style = character.get('communication_style', {})
            
            # Check for specific template matches
            if intent == 'greeting' and templates.get('greeting'):
                greeting_templates = templates['greeting']
                if isinstance(greeting_templates, dict):
                    # Multi-language support
                    response_text = greeting_templates.get('tr') or greeting_templates.get('en', '')
                else:
                    response_text = str(greeting_templates)
                
                # Personalize with context
                user_name = self._extract_user_name_from_context(context)
                if user_name and '{name}' in response_text:
                    response_text = response_text.replace('{name}', user_name)
                
                return {
                    "text": self._process_dynamic_variables(response_text),
                    "confidence": 0.9,
                    "type": "character_greeting",
                    "character": character_id
                }
            
            elif intent == 'personal_info' and 'name' in user_input.lower():
                user_name = self._extract_user_name_from_input(user_input)
                if user_name:
                    # Learn the name
                    return {
                        "text": f"Memnun oldum {user_name}! Size nasıl yardımcı olabilirim?",
                        "confidence": 0.85,
                        "type": "name_recognition",
                        "learned_info": {"name": user_name}
                    }
            
            elif intent == 'question' and 'adım' in user_input.lower():
                user_name = self._extract_user_name_from_context(context)
                if user_name:
                    return {
                        "text": f"Adınız {user_name} olarak hatırlıyorum.",
                        "confidence": 0.9,
                        "type": "context_recall"
                    }
                else:
                    return {
                        "text": "Daha önce adınızı söylemediğinizi hatırlıyorum.",
                        "confidence": 0.7,
                        "type": "context_recall"
                    }
            
            # Personality-based adjustments
            friendly_level = personality.get('friendly', 0.5)
            humorous_level = personality.get('humorous', 0.5)
            
            if intent == 'help' and templates.get('help'):
                help_templates = templates['help']
                if isinstance(help_templates, dict):
                    response_text = help_templates.get('tr') or help_templates.get('en', '')
                else:
                    response_text = str(help_templates)
                
                # Add humor based on personality
                if humorous_level > 0.7 and random.random() < 0.3:
                    response_text += " " + random.choice([
                        "Yardımcı olmaktan memnuniyet duyarım!",
                        "Ne mutlu bana, bir şey öğreteceğim!",
                        "Hazırım patron! Ne yapmamı istersin?"
                    ])
                
                return {
                    "text": self._process_dynamic_variables(response_text),
                    "confidence": 0.8,
                    "type": "character_help",
                    "character": character_id
                }
            
        except Exception as e:
            self.logger.debug(f"Character response generation skipped: {e}")
        
        return None
    
    def _generate_intent_response(self, user_input: str, intent: str, 
                                context: List[Dict]) -> Optional[Dict[str, Any]]:
        """
        Generate intent-based response
        
        Args:
            user_input (str): User input
            intent (str): Primary intent
            context (List): Conversation context
            
        Returns:
            Dict or None: Intent-based response
        """
        try:
            user_input_lower = user_input.lower()
            
            if intent == 'greeting':
                greetings = [
                    "Merhaba! Size nasıl yardımcı olabilirim?",
                    "Selam! Ne yapabilirim?",
                    "Merhaba, memnun oldum!",
                    "Günaydın! Hazır mısınız?"
                ]
                return {
                    "text": random.choice(greetings),
                    "confidence": 0.8,
                    "type": "generic_greeting"
                }
            
            elif intent == 'time_query':
                if any(word in user_input_lower for word in ['saat', 'time', 'now']):
                    current_time = datetime.now().strftime('%H:%M:%S')
                    return {
                        "text": f"Şu anda saat: {current_time}",
                        "confidence": 0.95,
                        "type": "time_response"
                    }
                elif any(word in user_input_lower for word in ['tarih', 'date', 'gün']):
                    current_date = datetime.now().strftime('%d.%m.%Y')
                    day_name = datetime.now().strftime('%A')
                    turkish_days = {
                        'Monday': 'Pazartesi', 'Tuesday': 'Salı', 'Wednesday': 'Çarşamba',
                        'Thursday': 'Perşembe', 'Friday': 'Cuma', 'Saturday': 'Cumartesi',
                        'Sunday': 'Pazar'
                    }
                    turkish_day = turkish_days.get(day_name, day_name)
                    return {
                        "text": f"Bugün {current_date} {turkish_day}",
                        "confidence": 0.95,
                        "type": "date_response"
                    }
            
            elif intent == 'help':
                help_responses = [
                    "Size şu konularda yardımcı olabilirim: zaman, tarih, temel sorular",
                    "Yardım için 'saat kaç?', 'bugün günlerden ne?' gibi sorular sorabilirsiniz",
                    "Ben bir AI asistanım. Size günlük görevlerde yardımcı olabilirim."
                ]
                return {
                    "text": random.choice(help_responses),
                    "confidence": 0.8,
                    "type": "generic_help"
                }
            
            elif intent == 'farewell':
                farewells = [
                    "Görüşmek üzere!",
                    "Hoşça kalın!",
                    "İyi günler dilerim!",
                    "Kendinize iyi bakın!"
                ]
                return {
                    "text": random.choice(farewells),
                    "confidence": 0.8,
                    "type": "generic_farewell"
                }
            
            elif intent == 'question':
                # Check for specific question types
                if any(word in user_input_lower for word in ['adın ne', 'ismin ne', 'sen kimsin']):
                    return {
                        "text": "Ben bir AI asistanıyım. Size yardımcı olmaktan memnuniyet duyarım!",
                        "confidence": 0.85,
                        "type": "identity_question"
                    }
                elif any(word in user_input_lower for word in ['naber', 'nasılsın', 'ne haber']):
                    responses = [
                        "Teşekkürler, iyiyim! Siz nasılsınız?",
                        "Harikayım! Size yardımcı olabilir miyim?",
                        "İyiyim, teşekkürler. Size nasıl yardımcı olabilirim?"
                    ]
                    return {
                        "text": random.choice(responses),
                        "confidence": 0.8,
                        "type": "wellbeing_question"
                    }
            
        except Exception as e:
            self.logger.debug(f"Intent response generation skipped: {e}")
        
        return None
    
    def _generate_template_response(self, user_input: str, intent: str,
                                  context: List[Dict], character: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Generate response from templates
        
        Args:
            user_input (str): User input
            intent (str): Primary intent
            context (List): Conversation context
            character (Dict): Character definition
            
        Returns:
            Dict or None: Template-based response
        """
        try:
            # Character-based templates
            if character and character.get('response_templates'):
                templates = character['response_templates']
                if intent in templates:
                    template = templates[intent]
                    if isinstance(template, dict):
                        # Multi-language
                        response_text = template.get('tr') or template.get('en', '')
                    else:
                        response_text = str(template)
                    
                    # Process dynamic variables
                    response_text = self._process_dynamic_variables(response_text)
                    
                    return {
                        "text": response_text,
                        "confidence": 0.85,
                        "type": "template_response",
                        "template_source": character.get('id', 'unknown')
                    }
            
            # Default templates
            default_templates = {
                'greeting': [
                    "Merhaba! Size nasıl yardımcı olabilirim?",
                    "Selam! Ne için buradasınız?",
                    "Günaydın! Size yardımcı olmaktan memnuniyet duyarım!"
                ],
                'question': [
                    "İlginç bir soru! Düşüneyim...",
                    "Bu güzel bir soru. Şöyle düşüneyim...",
                    "Harika soru! Size şöyle yardımcı olabilirim..."
                ],
                'help': [
                    "Size şu konularda yardımcı olabilirim: zaman, tarih, temel sorular",
                    "Yardım için bana her şeyi sorabilirsiniz!",
                    "Ben bir AI asistanım, size günlük görevlerde yardımcı olabilirim."
                ]
            }
            
            if intent in default_templates:
                response_text = random.choice(default_templates[intent])
                response_text = self._process_dynamic_variables(response_text)
                
                return {
                    "text": response_text,
                    "confidence": 0.7,
                    "type": "default_template"
                }
            
        except Exception as e:
            self.logger.debug(f"Template response generation skipped: {e}")
        
        return None
    
    def _generate_fallback_response(self, user_input: str) -> Dict[str, Any]:
        """
        Generate fallback response when other methods fail
        
        Args:
            user_input (str): User input
            
        Returns:
            Dict: Fallback response
        """
        fallback_responses = [
            "Anlayamadım. 'yardım' yazarak neler yapabileceğimi öğrenebilirsiniz.",
            "Üzgünüm, tam olarak ne demek istediğinizi anlamadım. Tekrar deneyebilir misiniz?",
            "İlginç! Ama tam olarak ne istediğini anlamadım. Daha açıklayıcı olabilir misin?",
            "Hmm, bu konuda biraz kafa karıştırıcıydınız. Başka nasıl yardımcı olabilirim?"
        ]
        
        return {
            "text": random.choice(fallback_responses),
            "confidence": 0.3,
            "type": "fallback_response"
        }
    
    def _generate_error_response(self, error_message: str) -> Dict[str, Any]:
        """
        Generate error response
        
        Args:
            error_message (str): Error message
            
        Returns:
            Dict: Error response
        """
        return {
            "text": "Bir hata oluştu, lütfen tekrar deneyin.",
            "confidence": 0.0,
            "type": "error_response",
            "error": error_message
        }
    
    def _extract_user_name_from_context(self, context: List[Dict]) -> Optional[str]:
        """
        Extract user name from conversation context
        
        Args:
            context (List): Conversation context
            
        Returns:
            str or None: User name if found
        """
        if not context:
            return None
        
        # Look through recent context for name mentions
        for item in reversed(context[:3]):  # Check last 3 interactions
            user_input = item.get('user_input', '').lower()
            if 'adım' in user_input or 'ismim' in user_input or 'my name is' in user_input:
                # Simple name extraction
                words = user_input.split()
                if 'adım' in user_input:
                    try:
                        name_index = words.index('adım') + 1
                        if name_index < len(words):
                            return words[name_index].capitalize()
                    except ValueError:
                        pass
                elif 'my name is' in user_input:
                    try:
                        name_index = words.index('is') + 1
                        if name_index < len(words):
                            return words[name_index].capitalize()
                    except ValueError:
                        pass
        
        return None
    
    def _extract_user_name_from_input(self, user_input: str) -> Optional[str]:
        """
        Extract user name directly from input
        
        Args:
            user_input (str): User input
            
        Returns:
            str or None: User name if found
        """
        user_input_lower = user_input.lower()
        
        if 'adım' in user_input_lower:
            words = user_input_lower.split()
            try:
                name_index = words.index('adım') + 1
                if name_index < len(words):
                    return user_input.split()[name_index].capitalize()
            except ValueError:
                pass
        
        elif 'my name is' in user_input_lower:
            words = user_input_lower.split()
            try:
                name_index = words.index('is') + 1
                if name_index < len(words):
                    return user_input.split()[name_index].capitalize()
            except ValueError:
                pass
        
        return None
    
    def _process_dynamic_variables(self, text: str) -> str:
        """
        Process dynamic variables in response text
        
        Args:
            text (str): Response text with variables
            
        Returns:
            str: Processed text
        """
        try:
            # Replace known dynamic variables
            for var_name, var_func in self.dynamic_variables.items():
                placeholder = f'{{{var_name}}}'
                if placeholder in text:
                    try:
                        value = var_func()
                        text = text.replace(placeholder, str(value))
                    except Exception as e:
                        self.logger.debug(f"Error processing variable {var_name}: {e}")
            
            return text
        except Exception as e:
            self.logger.debug(f"Dynamic variable processing skipped: {e}")
            return text
    
    def add_custom_template(self, intent: str, templates: List[str], character_id: str = None):
        """
        Add custom response templates
        
        Args:
            intent (str): Intent type
            templates (List[str]): List of template strings
            character_id (str): Character identifier (optional)
        """
        try:
            cache_key = f"{character_id}_{intent}" if character_id else f"default_{intent}"
            self.template_cache[cache_key] = templates
            self.logger.info(f"Added {len(templates)} templates for intent '{intent}'")
        except Exception as e:
            self.logger.error(f"Error adding custom templates: {e}")
    
    def get_response_statistics(self) -> Dict[str, Any]:
        """
        Get response generation statistics
        
        Returns:
            Dict: Statistics about response generation
        """
        return {
            "template_cache_size": len(self.template_cache),
            "dynamic_variables_count": len(self.dynamic_variables),
            "generator_status": "active",
            "last_updated": datetime.now().isoformat()
        }

# Test function
def test_response_generator():
    """Test Response Generator functionality"""
    print("💬 Testing Response Generator...")
    
    # Create generator instance
    rg = ResponseGenerator()
    
    # Test intent analysis
    test_intents = [
        {"primary": "greeting", "confidence_scores": {"greeting": 0.9}},
        {"primary": "time_query", "confidence_scores": {"time_query": 0.8}},
        {"primary": "help", "confidence_scores": {"help": 0.7}}
    ]
    
    test_inputs = [
        "Merhaba",
        "Saat kaç?",
        "Yardım et",
        "Bugün günlerden ne?"
    ]
    
    # Test with different scenarios
    print("\n📝 Testing different response scenarios...")
    
    for i, (intent, user_input) in enumerate(zip(test_intents, test_inputs)):
        print(f"\nTest {i+1}: '{user_input}'")
        response = rg.generate_response(
            user_input=user_input,
            intent=intent,
            context=[],
            character=None
        )
        print(f"Response: {response['text']} (Confidence: {response['confidence']})")
    
    # Test with character
    print("\n🎭 Testing with character...")
    character = {
        "id": "artemis",
        "response_templates": {
            "greeting": {
                "tr": "Merhaba {name}! Size nasıl yardımcı olabilirim?",
                "en": "Hello {name}! How can I help you today?"
            }
        },
        "personality_traits": {
            "friendly": 0.8,
            "humorous": 0.6
        }
    }
    
    response = rg.generate_response(
        user_input="Merhaba",
        intent={"primary": "greeting", "confidence_scores": {"greeting": 0.9}},
        context=[],
        character=character
    )
    print(f"Character response: {response['text']}")
    
    # Test statistics
    print("\n📊 Testing statistics...")
    stats = rg.get_response_statistics()
    print(f"Response stats: {stats}")
    
    print("\n✅ Response Generator test completed!")

if __name__ == "__main__":
    test_response_generator()
