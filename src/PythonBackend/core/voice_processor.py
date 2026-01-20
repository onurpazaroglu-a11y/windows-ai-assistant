"""
Voice Processor for Windows AI Assistant
Handles speech recognition and text-to-speech functionality
"""

import pyttsx3
import threading
import logging
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime

# Try to import speech recognition - handle missing dependencies gracefully
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  SpeechRecognition not available: {e}")
    sr = None
    SPEECH_RECOGNITION_AVAILABLE = False

class VoiceProcessor:
    """Handle speech recognition and text-to-speech operations"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize Voice Processor
        
        Args:
            config (Dict): Voice processor configuration
        """
        self.logger = self._setup_logger()
        self.config = config or self._get_default_config()
        
        # Speech recognition components (conditional)
        self.recognizer = None
        self.microphone = None
        self.speech_recognition_enabled = False
        
        # Text-to-speech components
        self.tts_engine = None
        self.tts_initialized = False
        
        # State management
        self.is_listening = False
        self.is_speaking = False
        self.wake_word_active = self.config.get('wake_word_active', True)
        self.wake_word = self.config.get('wake_word', 'hey assistant').lower()
        
        # Callbacks
        self.speech_callback = None
        self.error_callback = None
        
        # Initialize components
        self._initialize_components()
        
        self.logger.info("VoiceProcessor initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the voice processor"""
        logger = logging.getLogger('VoiceProcessor')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default voice processor configuration"""
        return {
            'language': 'tr-TR',  # Turkish default, can be 'en-US', 'de-DE', etc.
            'energy_threshold': 300,
            'pause_threshold': 0.8,
            'phrase_time_limit': 10,
            'wake_word_active': True,
            'wake_word': 'hey assistant',
            'tts_voice_gender': 'female',
            'tts_rate': 200,
            'tts_volume': 0.8,
            'microphone_index': None,  # Auto-detect
            'recognizer_backend': 'google'  # google, sphinx, azure, etc.
        }
    
    def _initialize_components(self):
        """Initialize voice components based on available libraries"""
        # Initialize TTS
        self._initialize_tts()
        
        # Initialize speech recognition if available
        if SPEECH_RECOGNITION_AVAILABLE:
            try:
                self.recognizer = sr.Recognizer()
                self.microphone = sr.Microphone()
                self.speech_recognition_enabled = True
                
                # Adjust for ambient noise
                self._adjust_for_ambient_noise()
                self.logger.info("✅ Speech recognition initialized")
                
            except Exception as e:
                self.logger.warning(f"⚠️  Speech recognition initialization failed: {e}")
                self.speech_recognition_enabled = False
        else:
            self.logger.warning("⚠️  SpeechRecognition library not available")
            self.speech_recognition_enabled = False
    
    def _initialize_tts(self):
        """Initialize text-to-speech engine"""
        try:
            self.tts_engine = pyttsx3.init()
            
            # Configure TTS settings
            self.tts_engine.setProperty('rate', self.config.get('tts_rate', 200))
            self.tts_engine.setProperty('volume', self.config.get('tts_volume', 0.8))
            
            # Set voice based on gender preference
            voices = self.tts_engine.getProperty('voices')
            if voices:
                gender_pref = self.config.get('tts_voice_gender', 'female').lower()
                selected_voice = None
                
                # Try to find voice matching gender preference
                for voice in voices:
                    if gender_pref == 'female' and ('female' in voice.name.lower() or 'woman' in voice.name.lower()):
                        selected_voice = voice
                        break
                    elif gender_pref == 'male' and ('male' in voice.name.lower() or 'man' in voice.name.lower()):
                        selected_voice = voice
                        break
                
                # Fallback to first available voice
                if not selected_voice and voices:
                    selected_voice = voices[0]
                
                if selected_voice:
                    self.tts_engine.setProperty('voice', selected_voice.id)
            
            self.tts_initialized = True
            self.logger.info("✅ Text-to-speech engine initialized")
            
        except Exception as e:
            self.logger.error(f"❌ TTS initialization failed: {e}")
            self.tts_initialized = False
    
    def _adjust_for_ambient_noise(self):
        """Adjust recognizer for ambient noise"""
        if not self.speech_recognition_enabled or not self.microphone:
            return
            
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(
                    source, 
                    duration=self.config.get('ambient_adjust_duration', 1.0)
                )
                self.recognizer.energy_threshold = self.config.get('energy_threshold', 300)
                self.recognizer.pause_threshold = self.config.get('pause_threshold', 0.8)
            self.logger.info("✅ Ambient noise adjustment completed")
        except Exception as e:
            self.logger.warning(f"⚠️  Ambient noise adjustment failed: {e}")
    
    def set_speech_callback(self, callback: Callable[[str], None]):
        """
        Set callback function for speech recognition
        
        Args:
            callback (Callable): Function to call with recognized text
        """
        self.speech_callback = callback
        self.logger.info("Speech callback set")
    
    def set_error_callback(self, callback: Callable[[str], None]):
        """
        Set callback function for errors
        
        Args:
            callback (Callable): Function to call with error messages
        """
        self.error_callback = callback
        self.logger.info("Error callback set")
    
    def start_listening(self, continuous: bool = True) -> bool:
        """
        Start voice recognition listening
        
        Args:
            continuous (bool): Whether to listen continuously
            
        Returns:
            bool: Success status
        """
        if not self.speech_recognition_enabled:
            self.logger.error("❌ Speech recognition not available")
            if self.error_callback:
                self.error_callback("Speech recognition not available")
            return False
        
        if self.is_listening:
            self.logger.warning("Already listening")
            return False
        
        self.is_listening = True
        self.logger.info("🎤 Starting voice recognition listening")
        
        if continuous:
            # Start continuous listening in separate thread
            self.listening_thread = threading.Thread(
                target=self._continuous_listening, 
                daemon=True
            )
            self.listening_thread.start()
        else:
            # Single recognition
            threading.Thread(
                target=self._single_recognition, 
                daemon=True
            ).start()
        
        return True
    
    def stop_listening(self):
        """Stop voice recognition listening"""
        self.is_listening = False
        self.logger.info("⏹️  Stopped voice recognition listening")
    
    def _continuous_listening(self):
        """Continuously listen for voice input"""
        if not self.speech_recognition_enabled:
            return
            
        self.logger.info("👂 Continuous listening started")
        
        while self.is_listening:
            try:
                # Listen for audio
                with self.microphone as source:
                    self.logger.debug("Listening for audio...")
                    audio = self.recognizer.listen(
                        source,
                        phrase_time_limit=self.config.get('phrase_time_limit', 10)
                    )
                
                # Process the audio
                self._process_audio(audio)
                
            except Exception as e:
                self.logger.error(f"Error in continuous listening: {e}")
                if self.error_callback:
                    self.error_callback(f"Listening error: {str(e)}")
                
                # Brief pause before retrying
                time.sleep(0.1)
    
    def _single_recognition(self):
        """Single voice recognition attempt"""
        if not self.speech_recognition_enabled:
            return
            
        try:
            self.logger.info("👂 Listening for single phrase...")
            with self.microphone as source:
                audio = self.recognizer.listen(
                    source,
                    phrase_time_limit=self.config.get('phrase_time_limit', 10)
                )
            
            self._process_audio(audio)
            
        except Exception as e:
            self.logger.error(f"Single recognition error: {e}")
            if self.error_callback:
                self.error_callback(f"Recognition error: {str(e)}")
        finally:
            self.is_listening = False
    
    def _process_audio(self, audio):
        """Process audio and convert to text"""
        if not self.speech_recognition_enabled or not self.recognizer:
            return
            
        try:
            self.logger.debug("🔊 Processing audio for recognition...")
            
            # Recognize speech using configured backend
            backend = self.config.get('recognizer_backend', 'google')
            language = self.config.get('language', 'tr-TR')
            
            if backend == 'google':
                # Google Speech Recognition
                text = self.recognizer.recognize_google(audio, language=language)
            elif backend == 'sphinx':
                # CMU Sphinx (offline)
                text = self.recognizer.recognize_sphinx(audio, language=language)
            else:
                # Fallback to Google
                text = self.recognizer.recognize_google(audio, language=language)
            
            text = text.strip()
            self.logger.info(f"🗣️  Recognized speech: '{text}'")
            
            # Check for wake word if active
            if self.wake_word_active:
                if self.wake_word in text.lower():
                    self.logger.info("🔔 Wake word detected")
                    # Remove wake word and process remaining text
                    cleaned_text = text.lower().replace(self.wake_word, '').strip()
                    if cleaned_text:
                        self._handle_recognized_speech(cleaned_text)
                    else:
                        # Just wake word, acknowledge it
                        self.speak("Yes, how can I help you?")
                else:
                    self.logger.debug("Wake word not detected in speech")
            else:
                # Process all speech when wake word is disabled
                self._handle_recognized_speech(text)
                
        except sr.UnknownValueError:
            self.logger.warning("⚠️  Could not understand audio")
            if self.error_callback:
                self.error_callback("Sorry, I couldn't understand that.")
        except sr.RequestError as e:
            self.logger.error(f"❌ Speech recognition request error: {e}")
            if self.error_callback:
                self.error_callback("Speech recognition service error.")
        except Exception as e:
            self.logger.error(f"❌ Audio processing error: {e}")
            if self.error_callback:
                self.error_callback(f"Audio processing error: {str(e)}")
    
    def _handle_recognized_speech(self, text: str):
        """Handle recognized speech text"""
        if self.speech_callback:
            self.speech_callback(text)
        else:
            self.logger.warning("No speech callback set")
    
    def speak(self, text: str, blocking: bool = False) -> bool:
        """
        Convert text to speech
        
        Args:
            text (str): Text to speak
            blocking (bool): Whether to wait for speech to complete
            
        Returns:
            bool: Success status
        """
        if not self.tts_initialized:
            self.logger.error("❌ TTS engine not initialized")
            return False
        
        if self.is_speaking:
            self.logger.warning("Already speaking")
            return False
        
        try:
            self.is_speaking = True
            self.logger.info(f"📢 Speaking: '{text}'")
            
            if blocking:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
            else:
                # Non-blocking speech in separate thread
                def speak_async():
                    try:
                        self.tts_engine.say(text)
                        self.tts_engine.runAndWait()
                    finally:
                        self.is_speaking = False
                
                speech_thread = threading.Thread(target=speak_async, daemon=True)
                speech_thread.start()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Text-to-speech error: {e}")
            self.is_speaking = False
            return False
    
    def speak_async(self, text: str, callback: Callable[[], None] = None):
        """
        Speak text asynchronously with completion callback
        
        Args:
            text (str): Text to speak
            callback (Callable): Function to call when speaking completes
        """
        def speak_with_callback():
            try:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
                if callback:
                    callback()
            except Exception as e:
                self.logger.error(f"TTS async error: {e}")
                if self.error_callback:
                    self.error_callback(f"TTS error: {str(e)}")
            finally:
                self.is_speaking = False
        
        if not self.tts_initialized or self.is_speaking:
            if self.error_callback:
                self.error_callback("TTS busy or not initialized")
            return
        
        self.is_speaking = True
        speech_thread = threading.Thread(target=speak_with_callback, daemon=True)
        speech_thread.start()
    
    def set_language(self, language_code: str):
        """
        Set recognition language
        
        Args:
            language_code (str): Language code (e.g., 'tr-TR', 'en-US')
        """
        self.config['language'] = language_code
        self.logger.info(f"Language set to: {language_code}")
    
    def set_wake_word(self, wake_word: str, active: bool = True):
        """
        Set wake word configuration
        
        Args:
            wake_word (str): Wake word phrase
            active (bool): Whether wake word detection is active
        """
        self.wake_word = wake_word.lower()
        self.wake_word_active = active
        self.logger.info(f"Wake word set to: '{wake_word}' (active: {active})")
    
    def set_tts_properties(self, rate: int = None, volume: float = None, voice_gender: str = None):
        """
        Set text-to-speech properties
        
        Args:
            rate (int): Speech rate (words per minute)
            volume (float): Volume level (0.0-1.0)
            voice_gender (str): Voice gender preference ('male' or 'female')
        """
        try:
            if rate is not None:
                self.tts_engine.setProperty('rate', rate)
                self.config['tts_rate'] = rate
            
            if volume is not None:
                self.tts_engine.setProperty('volume', volume)
                self.config['tts_volume'] = volume
            
            if voice_gender is not None:
                self.config['tts_voice_gender'] = voice_gender
                # Re-initialize to apply voice gender
                voices = self.tts_engine.getProperty('voices')
                if voices:
                    for voice in voices:
                        if voice_gender.lower() in voice.name.lower():
                            self.tts_engine.setProperty('voice', voice.id)
                            break
            
            self.logger.info("TTS properties updated")
            
        except Exception as e:
            self.logger.error(f"Error setting TTS properties: {e}")
    
    def get_voice_devices(self) -> Dict[str, Any]:
        """
        Get available voice input/output devices
        
        Returns:
            Dict: Information about available devices
        """
        if not self.speech_recognition_enabled:
            return {'error': 'Speech recognition not available'}
            
        try:
            # Get microphone list
            mic_list = sr.Microphone.list_microphone_names()
            
            # Get TTS voices
            if self.tts_engine:
                voices = self.tts_engine.getProperty('voices')
                voice_list = [{'id': v.id, 'name': v.name, 'gender': getattr(v, 'gender', 'unknown')} for v in voices]
            else:
                voice_list = []
            
            return {
                'microphones': mic_list,
                'tts_voices': voice_list,
                'current_mic_index': self.config.get('microphone_index'),
                'tts_initialized': self.tts_initialized
            }
            
        except Exception as e:
            self.logger.error(f"Error getting voice devices: {e}")
            return {'error': str(e)}
    
    def test_microphone(self) -> Dict[str, Any]:
        """
        Test microphone functionality
        
        Returns:
            Dict: Test results
        """
        if not self.speech_recognition_enabled:
            return {'success': False, 'error': 'Speech recognition not available'}
            
        try:
            self.logger.info("🎤 Testing microphone...")
            
            with self.microphone as source:
                # Test ambient noise adjustment
                start_time = time.time()
                self.recognizer.adjust_for_ambient_noise(source, duration=1.0)
                adjust_time = time.time() - start_time
                
                # Test audio capture
                audio = self.recognizer.listen(source, timeout=3, phrase_time_limit=2)
                capture_success = True
            
            return {
                'success': True,
                'ambient_adjustment_time': adjust_time,
                'audio_capture': capture_success,
                'energy_threshold': self.recognizer.energy_threshold,
                'message': 'Microphone test completed successfully'
            }
            
        except Exception as e:
            self.logger.error(f"Microphone test failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Microphone test failed'
            }
    
    def calibrate_wake_word_sensitivity(self, duration: int = 5) -> Dict[str, Any]:
        """
        Calibrate wake word sensitivity based on ambient noise
        
        Args:
            duration (int): Calibration duration in seconds
            
        Returns:
            Dict: Calibration results
        """
        if not self.speech_recognition_enabled:
            return {'success': False, 'error': 'Speech recognition not available'}
            
        try:
            self.logger.info("📊 Calibrating wake word sensitivity...")
            
            with self.microphone as source:
                # Measure ambient noise levels
                start_time = time.time()
                while time.time() - start_time < duration:
                    try:
                        audio = self.recognizer.listen(source, timeout=1)
                        # In a real implementation, you'd analyze the audio levels here
                        self.logger.debug("Calibration sample captured")
                    except sr.WaitTimeoutError:
                        continue
            
            # Adjust energy threshold based on ambient levels
            # This is a simplified approach - real implementation would be more sophisticated
            current_threshold = self.recognizer.energy_threshold
            new_threshold = current_threshold * 1.2  # Increase sensitivity slightly
            
            self.recognizer.energy_threshold = new_threshold
            self.config['energy_threshold'] = new_threshold
            
            return {
                'success': True,
                'original_threshold': current_threshold,
                'new_threshold': new_threshold,
                'message': f'Wake word sensitivity calibrated. New threshold: {new_threshold}'
            }
            
        except Exception as e:
            self.logger.error(f"Wake word calibration failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'message': 'Wake word calibration failed'
            }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get voice processor status
        
        Returns:
            Dict: Current status information
        """
        return {
            'listening': self.is_listening,
            'speaking': self.is_speaking,
            'tts_initialized': self.tts_initialized,
            'speech_recognition_enabled': self.speech_recognition_enabled,
            'wake_word_active': self.wake_word_active,
            'wake_word': self.wake_word,
            'language': self.config.get('language', 'tr-TR'),
            'energy_threshold': self.recognizer.energy_threshold if self.recognizer else None,
            'config': self.config
        }

# Test function with graceful fallback
def test_voice_processor():
    """Test Voice Processor functionality"""
    print("🎙️  Testing Voice Processor...")
    
    # Create processor instance
    vp = VoiceProcessor()
    
    # Test TTS even if speech recognition is not available
    print("\n🔊 Testing text-to-speech...")
    if vp.tts_initialized:
        success = vp.speak("Hello! This is a test of the text-to-speech system.", blocking=True)
        print(f"TTS test: {'✅ Success' if success else '❌ Failed'}")
    else:
        print("❌ TTS not available")
    
    # Test speech recognition if available
    if vp.speech_recognition_enabled:
        print("\n🎤 Testing microphone...")
        mic_test = vp.test_microphone()
        print(f"Microphone test: {mic_test}")
        
        # Test device enumeration
        print("\n🎧 Testing device enumeration...")
        devices = vp.get_voice_devices()
        print(f"Devices: {devices}")
        
        # Test calibration
        print("\n📊 Testing wake word calibration...")
        calibration = vp.calibrate_wake_word_sensitivity(2)
        print(f"Calibration: {calibration}")
    else:
        print("\n⚠️  Speech recognition not available - skipping related tests")
    
    # Test status
    print("\n📊 Testing status...")
    status = vp.get_status()
    print(f"Status: {status}")
    
    print("\n✅ Voice Processor test completed!")

if __name__ == "__main__":
    test_voice_processor()
