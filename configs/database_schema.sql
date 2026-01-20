-- Context Manager Database Schema
CREATE TABLE conversation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    user_input TEXT,
    ai_response TEXT,
    context_hash TEXT,
    profile_id TEXT,
    character_id TEXT
);

CREATE TABLE user_preferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    preference_key TEXT,
    preference_value TEXT,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE learned_facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fact_key TEXT UNIQUE,
    fact_value TEXT,
    confidence REAL,
    source TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_used DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_facts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    fact_key TEXT,
    fact_value TEXT,
    confidence REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_confirmed DATETIME DEFAULT CURRENT_TIMESTAMP
);
