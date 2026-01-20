"""
Context Manager for Windows AI Assistant
Handles conversation history, user preferences, and contextual awareness
"""

import json
import sqlite3
import hashlib
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

class ContextManager:
    """Manage conversation context and user preferences"""
    
    def __init__(self, db_path: str = "../databases/context.db"):
        """
        Initialize Context Manager
        
        Args:
            db_path (str): Path to SQLite database file
        """
        self.logger = self._setup_logger()
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()
        self.logger.info("ContextManager initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the context manager"""
        logger = logging.getLogger('ContextManager')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger
    
    def _initialize_database(self):
        """Initialize SQLite database with required tables"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Conversation history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_input TEXT,
                    ai_response TEXT,
                    context_hash TEXT,
                    profile_id TEXT,
                    character_id TEXT
                )
            ''')
            
            # User preferences table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    preference_key TEXT,
                    preference_value TEXT,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Learned facts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learned_facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fact_key TEXT UNIQUE,
                    fact_value TEXT,
                    confidence REAL,
                    source TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_used DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # User facts table (personal information)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    fact_key TEXT,
                    fact_value TEXT,
                    confidence REAL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_confirmed DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info("✅ Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Database initialization error: {e}")
            raise
    
    def store_interaction(self, session_id: str, user_input: str, ai_response: str, 
                         intent: Dict[str, Any] = None, profile_id: str = None, 
                         character_id: str = None) -> bool:
        """
        Store conversation interaction in database
        
        Args:
            session_id (str): Session identifier
            user_input (str): User's input text
            ai_response (str): AI's response text
            intent (Dict): Intent analysis data
            profile_id (str): Current profile ID
            character_id (str): Current character ID
            
        Returns:
            bool: Success status
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Create context hash
            context_hash = hashlib.md5(f"{user_input}{ai_response}".encode()).hexdigest()
            
            cursor.execute('''
                INSERT INTO conversation_history 
                (session_id, user_input, ai_response, context_hash, profile_id, character_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (session_id, user_input, ai_response, context_hash, profile_id, character_id))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"✅ Stored interaction for session {session_id}")
            
            # Extract and learn facts from conversation
            self._extract_facts_from_interaction(user_input, ai_response, intent)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error storing interaction: {e}")
            return False
    
    def _extract_facts_from_interaction(self, user_input: str, ai_response: str, intent: Dict[str, Any]):
        """
        Extract potential facts from conversation for learning
        
        Args:
            user_input (str): User's input
            ai_response (str): AI's response
            intent (Dict): Intent analysis data
        """
        try:
            user_input_lower = user_input.lower()
            
            # Name extraction
            if "adım" in user_input_lower or "benim adım" in user_input_lower or "my name is" in user_input_lower:
                # Simple name extraction (in real implementation, use NLP)
                words = user_input.split()
                if len(words) > 1:
                    potential_name = words[-1] if "adım" in user_input_lower else words[-1]
                    self.learn_user_fact("name", potential_name, confidence=0.8, source="conversation")
            
            # Preference extraction
            if "beğen" in user_input_lower or "like" in user_input_lower:
                # Extract preferences (simplified)
                if "müzik" in user_input_lower or "music" in user_input_lower:
                    self.set_user_preference("interest_music", "true")
                elif "spor" in user_input_lower or "sports" in user_input_lower:
                    self.set_user_preference("interest_sports", "true")
                    
        except Exception as e:
            self.logger.debug(f"Fact extraction skipped: {e}")
    
    def get_context(self, session_id: str, current_input: str = None, max_history: int = 5) -> List[Dict[str, Any]]:
        """
        Get relevant context for current session
        
        Args:
            session_id (str): Session identifier
            current_input (str): Current user input for relevance calculation
            max_history (int): Maximum number of history items to return
            
        Returns:
            List[Dict]: List of context items
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT user_input, ai_response, timestamp, profile_id, character_id
                FROM conversation_history 
                WHERE session_id = ?
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (session_id, max_history))
            
            rows = cursor.fetchall()
            conn.close()
            
            context_items = []
            for row in rows:
                context_items.append({
                    'user_input': row[0],
                    'ai_response': row[1],
                    'timestamp': row[2],
                    'profile_id': row[3],
                    'character_id': row[4]
                })
            
            self.logger.debug(f"Retrieved {len(context_items)} context items for session {session_id}")
            return context_items
            
        except Exception as e:
            self.logger.error(f"Error retrieving context: {e}")
            return []
    
    def get_recent_context(self, hours: int = 24, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent context from all sessions
        
        Args:
            hours (int): Hours to look back
            limit (int): Maximum items to return
            
        Returns:
            List[Dict]: Recent context items
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            since_time = datetime.now() - timedelta(hours=hours)
            
            cursor.execute('''
                SELECT session_id, user_input, ai_response, timestamp, profile_id, character_id
                FROM conversation_history 
                WHERE timestamp > ?
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (since_time, limit))
            
            rows = cursor.fetchall()
            conn.close()
            
            context_items = []
            for row in rows:
                context_items.append({
                    'session_id': row[0],
                    'user_input': row[1],
                    'ai_response': row[2],
                    'timestamp': row[3],
                    'profile_id': row[4],
                    'character_id': row[5]
                })
            
            return context_items
            
        except Exception as e:
            self.logger.error(f"Error retrieving recent context: {e}")
            return []
    
    def set_user_preference(self, user_id: str, key: str, value: str) -> bool:
        """
        Set user preference
        
        Args:
            user_id (str): User identifier
            key (str): Preference key
            value (str): Preference value
            
        Returns:
            bool: Success status
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_preferences 
                (user_id, preference_key, preference_value, last_updated)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, key, value))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Set preference for user {user_id}: {key} = {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting preference: {e}")
            return False
    
    def get_user_preference(self, user_id: str, key: str) -> Optional[str]:
        """
        Get user preference
        
        Args:
            user_id (str): User identifier
            key (str): Preference key
            
        Returns:
            str or None: Preference value or None if not found
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT preference_value FROM user_preferences
                WHERE user_id = ? AND preference_key = ?
                ORDER BY last_updated DESC
                LIMIT 1
            ''', (user_id, key))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return row[0]
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting preference: {e}")
            return None
    
    def get_all_user_preferences(self, user_id: str) -> Dict[str, str]:
        """
        Get all preferences for a user
        
        Args:
            user_id (str): User identifier
            
        Returns:
            Dict: Dictionary of all preferences
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT preference_key, preference_value FROM user_preferences
                WHERE user_id = ?
                ORDER BY last_updated DESC
            ''', (user_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            preferences = {}
            for key, value in rows:
                preferences[key] = value
            
            return preferences
            
        except Exception as e:
            self.logger.error(f"Error getting all preferences: {e}")
            return {}
    
    def learn_user_fact(self, user_id: str, fact_key: str, fact_value: str, 
                       confidence: float = 1.0, source: str = "user_input") -> bool:
        """
        Learn and store user-specific facts
        
        Args:
            user_id (str): User identifier
            fact_key (str): Fact key/name
            fact_value (str): Fact value
            confidence (float): Confidence level (0.0-1.0)
            source (str): Source of the fact
            
        Returns:
            bool: Success status
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_facts 
                (user_id, fact_key, fact_value, confidence, created_at, last_confirmed)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (user_id, fact_key, fact_value, confidence))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Learned fact for user {user_id}: {fact_key} = {fact_value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error learning user fact: {e}")
            return False
    
    def get_user_fact(self, user_id: str, fact_key: str) -> Optional[str]:
        """
        Get user-specific fact
        
        Args:
            user_id (str): User identifier
            fact_key (str): Fact key
            
        Returns:
            str or None: Fact value or None if not found
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT fact_value, confidence FROM user_facts
                WHERE user_id = ? AND fact_key = ?
                ORDER BY last_confirmed DESC
                LIMIT 1
            ''', (user_id, fact_key))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return row[0]  # Return just the fact value
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting user fact: {e}")
            return None
    
    def learn_general_fact(self, fact_key: str, fact_value: str, 
                          confidence: float = 1.0, source: str = "interaction") -> bool:
        """
        Learn and store general facts (not user-specific)
        
        Args:
            fact_key (str): Fact key/name
            fact_value (str): Fact value
            confidence (float): Confidence level (0.0-1.0)
            source (str): Source of the fact
            
        Returns:
            bool: Success status
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO learned_facts 
                (fact_key, fact_value, confidence, source, created_at, last_used)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ''', (fact_key, fact_value, confidence, source))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Learned general fact: {fact_key} = {fact_value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error learning general fact: {e}")
            return False
    
    def get_learned_fact(self, fact_key: str) -> Optional[str]:
        """
        Get learned general fact
        
        Args:
            fact_key (str): Fact key
            
        Returns:
            str or None: Fact value or None if not found
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT fact_value, confidence FROM learned_facts
                WHERE fact_key = ?
                ORDER BY last_used DESC
                LIMIT 1
            ''', (fact_key,))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                # Update last_used timestamp
                conn = sqlite3.connect(str(self.db_path))
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE learned_facts SET last_used = CURRENT_TIMESTAMP
                    WHERE fact_key = ?
                ''', (fact_key,))
                conn.commit()
                conn.close()
                
                return row[0]
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting learned fact: {e}")
            return None
    
    def clear_session_context(self, session_id: str) -> bool:
        """
        Clear context for specific session
        
        Args:
            session_id (str): Session identifier
            
        Returns:
            bool: Success status
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                DELETE FROM conversation_history WHERE session_id = ?
            ''', (session_id,))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Cleared context for session {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error clearing session context: {e}")
            return False
    
    def get_context_stats(self) -> Dict[str, Any]:
        """
        Get context statistics
        
        Returns:
            Dict: Statistics about stored context
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Total conversations
            cursor.execute('SELECT COUNT(*) FROM conversation_history')
            total_conversations = cursor.fetchone()[0]
            
            # Total users
            cursor.execute('SELECT COUNT(DISTINCT session_id) FROM conversation_history')
            total_sessions = cursor.fetchone()[0]
            
            # Total preferences
            cursor.execute('SELECT COUNT(*) FROM user_preferences')
            total_preferences = cursor.fetchone()[0]
            
            # Total learned facts
            cursor.execute('SELECT COUNT(*) FROM learned_facts')
            total_facts = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "total_conversations": total_conversations,
                "total_sessions": total_sessions,
                "total_preferences": total_preferences,
                "total_learned_facts": total_facts,
                "database_path": str(self.db_path)
            }
            
        except Exception as e:
            self.logger.error(f"Error getting context stats: {e}")
            return {}

# Test function
def test_context_manager():
    """Test Context Manager functionality"""
    print("🧠 Testing Context Manager...")
    
    # Create manager instance
    cm = ContextManager("../databases/test_context.db")
    
    # Test storing interaction
    print("\n📝 Testing interaction storage...")
    success = cm.store_interaction(
        session_id="test_session_1",
        user_input="Merhaba, benim adım Ahmet",
        ai_response="Merhaba Ahmet! Memnun oldum.",
        intent={"primary": "greeting"}
    )
    print(f"Store interaction: {'✅ Success' if success else '❌ Failed'}")
    
    # Test context retrieval
    print("\n🔍 Testing context retrieval...")
    context = cm.get_context("test_session_1")
    print(f"Retrieved context items: {len(context)}")
    if context:
        print(f"Latest context: {context[0]}")
    
    # Test user preferences
    print("\n⚙️  Testing user preferences...")
    pref_success = cm.set_user_preference("test_user", "language", "tr")
    print(f"Set preference: {'✅ Success' if pref_success else '❌ Failed'}")
    
    pref_value = cm.get_user_preference("test_user", "language")
    print(f"Retrieved preference: {pref_value}")
    
    # Test learning facts
    print("\n📚 Testing fact learning...")
    fact_success = cm.learn_user_fact("test_user", "favorite_color", "blue", 0.9)
    print(f"Learn fact: {'✅ Success' if fact_success else '❌ Failed'}")
    
    fact_value = cm.get_user_fact("test_user", "favorite_color")
    print(f"Retrieved fact: {fact_value}")
    
    # Test statistics
    print("\n📊 Testing statistics...")
    stats = cm.get_context_stats()
    print(f"Context stats: {stats}")
    
    print("\n✅ Context Manager test completed!")

if __name__ == "__main__":
    test_context_manager()
