"""
Database Manager for Windows AI Assistant
Enhanced database operations and optimization
"""

import sqlite3
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import threading

class DatabaseManager:
    """Enhanced database management with optimization and advanced features"""
    
    def __init__(self, db_path: str = "../databases/ai_assistant.db"):
        """
        Initialize Database Manager
        
        Args:
            db_path (str): Path to main database file
        """
        self.logger = self._setup_logger()
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection_pool = {}
        self.lock = threading.Lock()
        self._initialize_databases()
        self.logger.info("DatabaseManager initialized")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the database manager"""
        logger = logging.getLogger('DatabaseManager')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger
    
    def _initialize_databases(self):
        """Initialize all required database tables with enhanced schema"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Enhanced conversation history with indexing
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_input TEXT,
                    ai_response TEXT,
                    context_hash TEXT,
                    profile_id TEXT,
                    character_id TEXT,
                    intent_data TEXT,
                    response_confidence REAL,
                    processing_time_ms INTEGER
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_session_timestamp 
                ON conversation_history(session_id, timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_profile_character 
                ON conversation_history(profile_id, character_id)
            ''')
            
            # Enhanced user preferences with categories
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    category TEXT,
                    preference_key TEXT,
                    preference_value TEXT,
                    data_type TEXT,
                    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_persistent BOOLEAN DEFAULT TRUE
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_user_preferences 
                ON user_preferences(user_id, category, preference_key)
            ''')
            
            # Enhanced learned facts with categories and sources
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learned_facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fact_key TEXT UNIQUE,
                    fact_value TEXT,
                    category TEXT,
                    confidence REAL,
                    source TEXT,
                    learning_method TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_used DATETIME DEFAULT CURRENT_TIMESTAMP,
                    usage_count INTEGER DEFAULT 1
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_learned_facts_category 
                ON learned_facts(category, confidence)
            ''')
            
            # Enhanced user facts with verification
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    fact_key TEXT,
                    fact_value TEXT,
                    category TEXT,
                    confidence REAL,
                    source TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    last_confirmed DATETIME DEFAULT CURRENT_TIMESTAMP,
                    confirmation_count INTEGER DEFAULT 1,
                    is_verified BOOLEAN DEFAULT FALSE
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_user_facts_user 
                ON user_facts(user_id, category, fact_key)
            ''')
            
            # System metrics and analytics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    metric_name TEXT,
                    metric_value REAL,
                    category TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    session_id TEXT
                )
            ''')
            
            # Configuration settings table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_key TEXT UNIQUE,
                    config_value TEXT,
                    config_type TEXT,
                    description TEXT,
                    last_modified DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            self.logger.info("✅ Enhanced databases initialized successfully")
            
            # Initialize default configurations
            self._initialize_default_configs()
            
        except Exception as e:
            self.logger.error(f"❌ Database initialization error: {e}")
            raise
    
    def _initialize_default_configs(self):
        """Initialize default system configurations"""
        default_configs = [
            ("max_context_history", "50", "integer", "Maximum conversation history items to keep"),
            ("default_profile", "personal", "string", "Default profile on startup"),
            ("default_character", "artemis", "string", "Default character on startup"),
            ("auto_learning_enabled", "true", "boolean", "Enable automatic fact learning"),
            ("context_timeout_hours", "24", "integer", "Hours to keep context active"),
            ("max_db_connections", "10", "integer", "Maximum database connections"),
            ("backup_interval_minutes", "60", "integer", "Database backup interval")
        ]
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            for config_key, config_value, config_type, description in default_configs:
                cursor.execute('''
                    INSERT OR IGNORE INTO system_config 
                    (config_key, config_value, config_type, description)
                    VALUES (?, ?, ?, ?)
                ''', (config_key, config_value, config_type, description))
            
            conn.commit()
            conn.close()
            self.logger.info("✅ Default configurations initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Default config initialization error: {e}")
    
    def get_connection(self, connection_id: str = "default") -> sqlite3.Connection:
        """
        Get database connection with pooling
        
        Args:
            connection_id (str): Connection identifier
            
        Returns:
            sqlite3.Connection: Database connection
        """
        with self.lock:
            if connection_id not in self.connection_pool:
                conn = sqlite3.connect(str(self.db_path))
                conn.row_factory = sqlite3.Row  # Enable column access by name
                self.connection_pool[connection_id] = conn
                self.logger.debug(f"Created new database connection: {connection_id}")
            return self.connection_pool[connection_id]
    
    def close_connection(self, connection_id: str = "default"):
        """
        Close specific database connection
        
        Args:
            connection_id (str): Connection identifier
        """
        with self.lock:
            if connection_id in self.connection_pool:
                self.connection_pool[connection_id].close()
                del self.connection_pool[connection_id]
                self.logger.debug(f"Closed database connection: {connection_id}")
    
    def close_all_connections(self):
        """Close all database connections"""
        with self.lock:
            for conn_id, conn in self.connection_pool.items():
                try:
                    conn.close()
                    self.logger.debug(f"Closed connection: {conn_id}")
                except Exception as e:
                    self.logger.error(f"Error closing connection {conn_id}: {e}")
            self.connection_pool.clear()
    
    def store_conversation_with_metrics(self, session_id: str, user_input: str, 
                                      ai_response: str, intent_data: Dict[str, Any] = None,
                                      profile_id: str = None, character_id: str = None,
                                      response_confidence: float = 1.0, 
                                      processing_time_ms: int = 0) -> bool:
        """
        Store conversation with performance metrics
        
        Args:
            session_id (str): Session identifier
            user_input (str): User input text
            ai_response (str): AI response text
            intent_data (Dict): Intent analysis data
            profile_id (str): Profile identifier
            character_id (str): Character identifier
            response_confidence (float): Response confidence level
            processing_time_ms (int): Processing time in milliseconds
            
        Returns:
            bool: Success status
        """
        try:
            conn = self.get_connection(f"conv_{session_id}")
            cursor = conn.cursor()
            
            # Create context hash
            import hashlib
            context_hash = hashlib.md5(f"{user_input}{ai_response}".encode()).hexdigest()
            
            cursor.execute('''
                INSERT INTO conversation_history 
                (session_id, user_input, ai_response, context_hash, profile_id, character_id,
                 intent_data, response_confidence, processing_time_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, user_input, ai_response, context_hash, profile_id, character_id,
                  json.dumps(intent_data) if intent_data else None, response_confidence, processing_time_ms))
            
            conn.commit()
            
            self.logger.info(f"✅ Stored conversation with metrics for session {session_id}")
            
            # Store performance metrics
            self.store_metric("processing_time_ms", processing_time_ms, "performance", session_id)
            self.store_metric("response_confidence", response_confidence, "quality", session_id)
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error storing conversation: {e}")
            return False
    
    def get_conversation_history(self, session_id: str, limit: int = 50, 
                               hours_back: int = 24) -> List[Dict[str, Any]]:
        """
        Get conversation history with filtering options
        
        Args:
            session_id (str): Session identifier
            limit (int): Maximum number of records to return
            hours_back (int): Hours to look back
            
        Returns:
            List[Dict]: Conversation history
        """
        try:
            conn = self.get_connection(f"read_{session_id}")
            cursor = conn.cursor()
            
            since_time = datetime.now() - timedelta(hours=hours_back)
            
            cursor.execute('''
                SELECT session_id, user_input, ai_response, timestamp, 
                       profile_id, character_id, intent_data, response_confidence,
                       processing_time_ms
                FROM conversation_history 
                WHERE session_id = ? AND timestamp > ?
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (session_id, since_time, limit))
            
            rows = cursor.fetchall()
            
            history = []
            for row in rows:
                history.append({
                    'session_id': row['session_id'],
                    'user_input': row['user_input'],
                    'ai_response': row['ai_response'],
                    'timestamp': row['timestamp'],
                    'profile_id': row['profile_id'],
                    'character_id': row['character_id'],
                    'intent_data': json.loads(row['intent_data']) if row['intent_data'] else None,
                    'response_confidence': row['response_confidence'],
                    'processing_time_ms': row['processing_time_ms']
                })
            
            self.logger.debug(f"Retrieved {len(history)} conversation items for session {session_id}")
            return history
            
        except Exception as e:
            self.logger.error(f"Error retrieving conversation history: {e}")
            return []
    
    def store_metric(self, metric_name: str, metric_value: float, 
                    category: str = "general", session_id: str = None) -> bool:
        """
        Store system performance metrics
        
        Args:
            metric_name (str): Metric name
            metric_value (float): Metric value
            category (str): Metric category
            session_id (str): Session identifier
            
        Returns:
            bool: Success status
        """
        try:
            conn = self.get_connection("metrics")
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO system_metrics 
                (metric_name, metric_value, category, session_id)
                VALUES (?, ?, ?, ?)
            ''', (metric_name, metric_value, category, session_id))
            
            conn.commit()
            self.logger.debug(f"Stored metric: {metric_name} = {metric_value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error storing metric: {e}")
            return False
    
    def get_metrics_summary(self, category: str = None, hours_back: int = 24) -> Dict[str, Any]:
        """
        Get system metrics summary
        
        Args:
            category (str): Metric category filter
            hours_back (int): Hours to look back
            
        Returns:
            Dict: Metrics summary
        """
        try:
            conn = self.get_connection("metrics_read")
            cursor = conn.cursor()
            
            since_time = datetime.now() - timedelta(hours=hours_back)
            
            if category:
                cursor.execute('''
                    SELECT metric_name, AVG(metric_value) as avg_value, 
                           MIN(metric_value) as min_value, MAX(metric_value) as max_value,
                           COUNT(*) as count
                    FROM system_metrics 
                    WHERE category = ? AND timestamp > ?
                    GROUP BY metric_name
                ''', (category, since_time))
            else:
                cursor.execute('''
                    SELECT metric_name, AVG(metric_value) as avg_value, 
                           MIN(metric_value) as min_value, MAX(metric_value) as max_value,
                           COUNT(*) as count
                    FROM system_metrics 
                    WHERE timestamp > ?
                    GROUP BY metric_name
                ''', (since_time,))
            
            rows = cursor.fetchall()
            
            summary = {}
            for row in rows:
                summary[row['metric_name']] = {
                    'average': row['avg_value'],
                    'minimum': row['min_value'],
                    'maximum': row['max_value'],
                    'count': row['count']
                }
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error getting metrics summary: {e}")
            return {}
    
    def set_user_preference(self, user_id: str, category: str, key: str, 
                          value: str, data_type: str = "string") -> bool:
        """
        Set user preference with category support
        
        Args:
            user_id (str): User identifier
            category (str): Preference category
            key (str): Preference key
            value (str): Preference value
            data_type (str): Data type of value
            
        Returns:
            bool: Success status
        """
        try:
            conn = self.get_connection(f"prefs_{user_id}")
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_preferences 
                (user_id, category, preference_key, preference_value, data_type, last_updated)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, category, key, value, data_type))
            
            conn.commit()
            self.logger.info(f"Set preference for user {user_id}: {category}.{key} = {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting preference: {e}")
            return False
    
    def get_user_preference(self, user_id: str, category: str, key: str) -> Optional[str]:
        """
        Get user preference
        
        Args:
            user_id (str): User identifier
            category (str): Preference category
            key (str): Preference key
            
        Returns:
            str or None: Preference value or None if not found
        """
        try:
            conn = self.get_connection(f"prefs_read_{user_id}")
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT preference_value FROM user_preferences
                WHERE user_id = ? AND category = ? AND preference_key = ?
                ORDER BY last_updated DESC
                LIMIT 1
            ''', (user_id, category, key))
            
            row = cursor.fetchone()
            if row:
                return row['preference_value']
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting preference: {e}")
            return None
    
    def get_user_preferences_by_category(self, user_id: str, category: str) -> Dict[str, str]:
        """
        Get all user preferences for a specific category
        
        Args:
            user_id (str): User identifier
            category (str): Preference category
            
        Returns:
            Dict: Preferences dictionary
        """
        try:
            conn = self.get_connection(f"prefs_cat_{user_id}")
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT preference_key, preference_value FROM user_preferences
                WHERE user_id = ? AND category = ?
                ORDER BY last_updated DESC
            ''', (user_id, category))
            
            rows = cursor.fetchall()
            
            preferences = {}
            for row in rows:
                preferences[row['preference_key']] = row['preference_value']
            
            return preferences
            
        except Exception as e:
            self.logger.error(f"Error getting preferences by category: {e}")
            return {}
    
    def learn_fact_with_verification(self, fact_key: str, fact_value: str,
                                   category: str = "general", confidence: float = 1.0,
                                   source: str = "interaction", learning_method: str = "observation") -> bool:
        """
        Learn and store facts with verification support
        
        Args:
            fact_key (str): Fact key/name
            fact_value (str): Fact value
            category (str): Fact category
            confidence (float): Confidence level (0.0-1.0)
            source (str): Source of the fact
            learning_method (str): How the fact was learned
            
        Returns:
            bool: Success status
        """
        try:
            conn = self.get_connection("facts")
            cursor = conn.cursor()
            
            # Check if fact already exists
            cursor.execute('''
                SELECT id, usage_count FROM learned_facts WHERE fact_key = ?
            ''', (fact_key,))
            
            row = cursor.fetchone()
            if row:
                # Update existing fact
                usage_count = row['usage_count'] + 1
                cursor.execute('''
                    UPDATE learned_facts 
                    SET fact_value = ?, confidence = ?, source = ?, learning_method = ?,
                        last_used = CURRENT_TIMESTAMP, usage_count = ?
                    WHERE fact_key = ?
                ''', (fact_value, confidence, source, learning_method, usage_count, fact_key))
            else:
                # Insert new fact
                cursor.execute('''
                    INSERT INTO learned_facts 
                    (fact_key, fact_value, category, confidence, source, learning_method,
                     created_at, last_used, usage_count)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1)
                ''', (fact_key, fact_value, category, confidence, source, learning_method))
            
            conn.commit()
            self.logger.info(f"Learned fact: {fact_key} = {fact_value} (confidence: {confidence})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error learning fact: {e}")
            return False
    
    def get_fact(self, fact_key: str) -> Optional[Dict[str, Any]]:
        """
        Get learned fact with metadata
        
        Args:
            fact_key (str): Fact key
            
        Returns:
            Dict or None: Fact data or None if not found
        """
        try:
            conn = self.get_connection("facts_read")
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT fact_key, fact_value, category, confidence, source, 
                       learning_method, created_at, last_used, usage_count
                FROM learned_facts
                WHERE fact_key = ?
                ORDER BY last_used DESC
                LIMIT 1
            ''', (fact_key,))
            
            row = cursor.fetchone()
            if row:
                # Update last_used timestamp
                cursor.execute('''
                    UPDATE learned_facts SET last_used = CURRENT_TIMESTAMP
                    WHERE fact_key = ?
                ''', (fact_key,))
                conn.commit()
                
                return {
                    'key': row['fact_key'],
                    'value': row['fact_value'],
                    'category': row['category'],
                    'confidence': row['confidence'],
                    'source': row['source'],
                    'learning_method': row['learning_method'],
                    'created_at': row['created_at'],
                    'last_used': row['last_used'],
                    'usage_count': row['usage_count']
                }
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting fact: {e}")
            return None
    
    def get_config_value(self, config_key: str, default_value: str = None) -> str:
        """
        Get configuration value
        
        Args:
            config_key (str): Configuration key
            default_value (str): Default value if not found
            
        Returns:
            str: Configuration value
        """
        try:
            conn = self.get_connection("config")
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT config_value FROM system_config WHERE config_key = ?
            ''', (config_key,))
            
            row = cursor.fetchone()
            if row:
                return row['config_value']
            return default_value or ""
            
        except Exception as e:
            self.logger.error(f"Error getting config value: {e}")
            return default_value or ""
    
    def set_config_value(self, config_key: str, config_value: str, 
                        config_type: str = "string", description: str = "") -> bool:
        """
        Set configuration value
        
        Args:
            config_key (str): Configuration key
            config_value (str): Configuration value
            config_type (str): Configuration type
            description (str): Description of the configuration
            
        Returns:
            bool: Success status
        """
        try:
            conn = self.get_connection("config_write")
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO system_config 
                (config_key, config_value, config_type, description, last_modified)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (config_key, config_value, config_type, description))
            
            conn.commit()
            self.logger.info(f"Set config: {config_key} = {config_value}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting config value: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive database statistics
        
        Returns:
            Dict: Database statistics
        """
        try:
            conn = self.get_connection("stats")
            cursor = conn.cursor()
            
            stats = {}
            
            # Conversation history count
            cursor.execute('SELECT COUNT(*) FROM conversation_history')
            stats['total_conversations'] = cursor.fetchone()[0]
            
            # User preferences count
            cursor.execute('SELECT COUNT(*) FROM user_preferences')
            stats['total_preferences'] = cursor.fetchone()[0]
            
            # Learned facts count
            cursor.execute('SELECT COUNT(*) FROM learned_facts')
            stats['total_learned_facts'] = cursor.fetchone()[0]
            
            # User facts count
            cursor.execute('SELECT COUNT(*) FROM user_facts')
            stats['total_user_facts'] = cursor.fetchone()[0]
            
            # Active sessions
            cursor.execute('SELECT COUNT(DISTINCT session_id) FROM conversation_history')
            stats['active_sessions'] = cursor.fetchone()[0]
            
            # Average response confidence
            cursor.execute('SELECT AVG(response_confidence) FROM conversation_history')
            avg_confidence = cursor.fetchone()[0]
            stats['average_response_confidence'] = round(avg_confidence or 0, 3)
            
            # Database file size
            try:
                stats['database_size_mb'] = round(self.db_path.stat().st_size / (1024 * 1024), 2)
            except Exception:
                stats['database_size_mb'] = 0
            
            stats['database_path'] = str(self.db_path)
            stats['connection_pool_size'] = len(self.connection_pool)
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting database stats: {e}")
            return {}
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> Dict[str, int]:
        """
        Clean up old database records
        
        Args:
            days_to_keep (int): Days of data to keep
            
        Returns:
            Dict: Cleanup results
        """
        try:
            conn = self.get_connection("cleanup")
            cursor = conn.cursor()
            
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            results = {}
            
            # Clean conversation history
            cursor.execute('''
                DELETE FROM conversation_history WHERE timestamp < ?
            ''', (cutoff_date,))
            results['deleted_conversations'] = cursor.rowcount
            
            # Clean old metrics
            cursor.execute('''
                DELETE FROM system_metrics WHERE timestamp < ?
            ''', (cutoff_date,))
            results['deleted_metrics'] = cursor.rowcount
            
            conn.commit()
            self.logger.info(f"Cleaned up old data: {results}")
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}")
            return {}
    
    def backup_database(self, backup_path: str = None) -> bool:
        """
        Create database backup
        
        Args:
            backup_path (str): Backup file path (optional)
            
        Returns:
            bool: Success status
        """
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"{self.db_path.parent}/backup_ai_assistant_{timestamp}.db"
            
            backup_path = Path(backup_path)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Get connection to source database
            source_conn = self.get_connection("backup_source")
            
            # Create backup
            backup_conn = sqlite3.connect(str(backup_path))
            source_conn.backup(backup_conn)
            backup_conn.close()
            
            self.logger.info(f"Database backed up to: {backup_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error creating database backup: {e}")
            return False

# Test function
def test_database_manager():
    """Test Database Manager functionality"""
    print("💾 Testing Database Manager...")
    
    # Create manager instance
    db_manager = DatabaseManager("../databases/test_ai_assistant.db")
    
    # Test storing conversation with metrics
    print("\n📝 Testing conversation storage with metrics...")
    success = db_manager.store_conversation_with_metrics(
        session_id="test_session_1",
        user_input="Merhaba, benim adım Ahmet",
        ai_response="Merhaba Ahmet! Memnun oldum.",
        intent_data={"primary": "greeting", "confidence": 0.9},
        profile_id="personal",
        character_id="artemis",
        response_confidence=0.95,
        processing_time_ms=150
    )
    print(f"Store conversation: {'✅ Success' if success else '❌ Failed'}")
    
    # Test conversation history retrieval
    print("\n🔍 Testing conversation history retrieval...")
    history = db_manager.get_conversation_history("test_session_1", limit=10)
    print(f"Retrieved {len(history)} conversation items")
    if history:
        print(f"Latest item: {history[0]['user_input'][:50]}...")
    
    # Test metrics storage
    print("\n📊 Testing metrics storage...")
    metric_success = db_manager.store_metric("test_metric", 0.85, "testing", "test_session_1")
    print(f"Store metric: {'✅ Success' if metric_success else '❌ Failed'}")
    
    # Test user preferences
    print("\n⚙️  Testing user preferences...")
    pref_success = db_manager.set_user_preference("test_user", "appearance", "theme", "dark")
    print(f"Set preference: {'✅ Success' if pref_success else '❌ Failed'}")
    
    pref_value = db_manager.get_user_preference("test_user", "appearance", "theme")
    print(f"Retrieved preference: {pref_value}")
    
    # Test fact learning
    print("\n📚 Testing fact learning...")
    fact_success = db_manager.learn_fact_with_verification(
        "test_fact", "test_value", "testing", 0.9, "manual", "direct_input"
    )
    print(f"Learn fact: {'✅ Success' if fact_success else '❌ Failed'}")
    
    fact_data = db_manager.get_fact("test_fact")
    print(f"Retrieved fact: {fact_data}")
    
    # Test configuration
    print("\n🔧 Testing configuration...")
    config_success = db_manager.set_config_value("test_config", "test_value", "string", "Test configuration")
    print(f"Set config: {'✅ Success' if config_success else '❌ Failed'}")
    
    config_value = db_manager.get_config_value("test_config")
    print(f"Retrieved config: {config_value}")
    
    # Test statistics
    print("\n📈 Testing statistics...")
    stats = db_manager.get_database_stats()
    print(f"Database stats: {stats}")
    
    # Test cleanup
    print("\n🧹 Testing cleanup...")
    cleanup_results = db_manager.cleanup_old_data(1)  # Keep only 1 day
    print(f"Cleanup results: {cleanup_results}")
    
    print("\n✅ Database Manager test completed!")

if __name__ == "__main__":
    test_database_manager()
