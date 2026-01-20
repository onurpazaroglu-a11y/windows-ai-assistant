"""
Sync Service for Windows AI Assistant
Handles synchronization between Obsidian vault and database
"""

import os
import json
import yaml
import sqlite3
import hashlib
import logging
import time
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading

class SyncService:
    """Handle synchronization between Obsidian vault and database"""
    
    def __init__(self, vault_path: str = "../obsidian_vault", db_path: str = "../databases/ai_assistant.db"):
        """
        Initialize Sync Service
        
        Args:
            vault_path (str): Path to Obsidian vault
            db_path (str): Path to SQLite database
        """
        self.logger = self._setup_logger()
        self.vault_path = Path(vault_path)
        self.db_path = Path(db_path)
        self.is_syncing = False
        self.sync_interval = 30  # 30 seconds default
        self.sync_timer = None
        self.file_observer = None
        self.last_sync_time = None
        
        # Ensure paths exist
        self.vault_path.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database if needed
        self._initialize_sync_database()
        
        self.logger.info("SyncService initialized")
        self.logger.info(f"Vault path: {self.vault_path}")
        self.logger.info(f"Database path: {self.db_path}")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging for the sync service"""
        logger = logging.getLogger('SyncService')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger
    
    def _initialize_sync_database(self):
        """Initialize sync tracking database"""
        try:
            sync_db_path = self.db_path.parent / "sync_tracking.db"
            conn = sqlite3.connect(str(sync_db_path))
            cursor = conn.cursor()
            
            # Table to track file hashes and sync status
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS file_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE,
                    file_hash TEXT,
                    last_modified TIMESTAMP,
                    sync_status TEXT,
                    last_sync TIMESTAMP,
                    file_type TEXT
                )
            ''')
            
            # Table to track sync operations
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sync_operations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    operation_type TEXT,
                    file_path TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT,
                    details TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
            self.sync_db_path = sync_db_path
            self.logger.info("✅ Sync tracking database initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Sync database initialization error: {e}")
            raise
    
    def start_sync_service(self, auto_sync: bool = True, watch_files: bool = True) -> bool:
        """
        Start sync service
        
        Args:
            auto_sync (bool): Whether to enable automatic periodic sync
            watch_files (bool): Whether to watch for file changes
            
        Returns:
            bool: Success status
        """
        try:
            self.logger.info("🚀 Starting Sync Service...")
            
            # Start file watching if requested
            if watch_files:
                self._start_file_watching()
            
            # Start auto sync if requested
            if auto_sync:
                self._start_auto_sync()
            
            self.logger.info("✅ Sync Service started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Failed to start Sync Service: {e}")
            return False
    
    def stop_sync_service(self):
        """Stop sync service"""
        try:
            # Stop auto sync
            if self.sync_timer:
                self.sync_timer.cancel()
                self.sync_timer = None
            
            # Stop file watching
            if self.file_observer:
                self.file_observer.stop()
                self.file_observer.join()
                self.file_observer = None
            
            self.logger.info("⏹️  Sync Service stopped")
            
        except Exception as e:
            self.logger.error(f"❌ Error stopping Sync Service: {e}")
    
    def _start_file_watching(self):
        """Start watching Obsidian vault for file changes"""
        try:
            if not self.vault_path.exists():
                self.logger.warning(f"Vault path does not exist: {self.vault_path}")
                return
            
            class VaultEventHandler(FileSystemEventHandler):
                def __init__(self, sync_service):
                    self.sync_service = sync_service
                
                def on_modified(self, event):
                    if not event.is_directory:
                        self.sync_service.logger.info(f"📁 File changed: {event.src_path}")
                        # Debounce the sync to avoid too many rapid calls
                        if hasattr(self.sync_service, '_pending_sync_timer'):
                            self.sync_service._pending_sync_timer.cancel()
                        
                        self.sync_service._pending_sync_timer = threading.Timer(
                            2.0, self.sync_service.sync_vault_to_db
                        )
                        self.sync_service._pending_sync_timer.start()
                
                def on_created(self, event):
                    if not event.is_directory:
                        self.sync_service.logger.info(f"📁 File created: {event.src_path}")
                        self.sync_service.sync_vault_to_db()
                
                def on_deleted(self, event):
                    if not event.is_directory:
                        self.sync_service.logger.info(f"📁 File deleted: {event.src_path}")
                        self.sync_service.sync_vault_to_db()
            
            self.file_observer = Observer()
            event_handler = VaultEventHandler(self)
            self.file_observer.schedule(event_handler, str(self.vault_path), recursive=True)
            self.file_observer.start()
            
            self.logger.info("👀 File watching started")
            
        except Exception as e:
            self.logger.error(f"❌ File watching setup failed: {e}")
    
    def _start_auto_sync(self):
        """Start automatic periodic sync"""
        def sync_worker():
            while True:
                try:
                    time.sleep(self.sync_interval)
                    if not self.is_syncing:
                        self.logger.debug("⏰ Auto sync triggered")
                        self.sync_vault_to_db()
                except Exception as e:
                    self.logger.error(f"❌ Auto sync error: {e}")
        
        self.sync_timer = threading.Thread(target=sync_worker, daemon=True)
        self.sync_timer.start()
        
        self.logger.info(f"⏰ Auto sync started (every {self.sync_interval} seconds)")
    
    def sync_vault_to_db(self) -> Dict[str, Any]:
        """
        Synchronize Obsidian vault to database
        
        Returns:
            Dict: Sync results
        """
        if self.is_syncing:
            self.logger.warning("Sync already in progress")
            return {"status": "warning", "message": "Sync already in progress"}
        
        self.is_syncing = True
        sync_start_time = time.time()
        results = {
            "processed_files": 0,
            "updated_files": 0,
            "skipped_files": 0,
            "errors": [],
            "synced_categories": []
        }
        
        try:
            self.logger.info("🔄 Starting vault to database sync...")
            
            # Process different vault directories
            categories = [
                ("profiles", self._sync_profiles),
                ("characters", self._sync_characters),
                ("knowledge", self._sync_knowledge),
                ("templates", self._sync_templates)
            ]
            
            for category_name, sync_function in categories:
                try:
                    category_results = sync_function()
                    results["synced_categories"].append(category_name)
                    results["processed_files"] += category_results.get("processed", 0)
                    results["updated_files"] += category_results.get("updated", 0)
                    results["skipped_files"] += category_results.get("skipped", 0)
                    
                    if category_results.get("errors"):
                        results["errors"].extend(category_results["errors"])
                        
                except Exception as e:
                    error_msg = f"Error syncing {category_name}: {str(e)}"
                    self.logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            # Update sync tracking
            self._update_sync_tracking()
            
            sync_duration = time.time() - sync_start_time
            self.last_sync_time = datetime.now()
            
            self.logger.info(f"✅ Sync completed in {sync_duration:.2f} seconds")
            self.logger.info(f"📊 Results: {results['processed_files']} files processed, "
                           f"{results['updated_files']} updated, {results['skipped_files']} skipped")
            
            results["status"] = "success"
            results["duration_seconds"] = round(sync_duration, 2)
            results["timestamp"] = self.last_sync_time.isoformat()
            
        except Exception as e:
            self.logger.error(f"❌ Sync failed: {e}")
            results["status"] = "error"
            results["error"] = str(e)
            
        finally:
            self.is_syncing = False
        
        return results
    
    def _sync_profiles(self) -> Dict[str, Any]:
        """Sync profile files from vault to database"""
        results = {"processed": 0, "updated": 0, "skipped": 0, "errors": []}
        
        try:
            profiles_path = self.vault_path / "profiles"
            if not profiles_path.exists():
                profiles_path.mkdir(parents=True, exist_ok=True)
                self.logger.info("📁 Created profiles directory")
                return results
            
            for profile_file in profiles_path.glob("*.md"):
                try:
                    if self._should_sync_file(profile_file):
                        success = self._process_profile_file(profile_file)
                        if success:
                            results["updated"] += 1
                        else:
                            results["skipped"] += 1
                        results["processed"] += 1
                    else:
                        results["skipped"] += 1
                        results["processed"] += 1
                        
                except Exception as e:
                    error_msg = f"Error processing profile {profile_file.name}: {str(e)}"
                    self.logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            self.logger.info(f"👥 Profiles synced: {results['processed']} processed")
            
        except Exception as e:
            error_msg = f"Error in profile sync: {str(e)}"
            self.logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results
    
    def _sync_characters(self) -> Dict[str, Any]:
        """Sync character files from vault to database"""
        results = {"processed": 0, "updated": 0, "skipped": 0, "errors": []}
        
        try:
            characters_path = self.vault_path / "characters"
            if not characters_path.exists():
                characters_path.mkdir(parents=True, exist_ok=True)
                self.logger.info("🎭 Created characters directory")
                return results
            
            for character_file in characters_path.glob("*.md"):
                try:
                    if self._should_sync_file(character_file):
                        success = self._process_character_file(character_file)
                        if success:
                            results["updated"] += 1
                        else:
                            results["skipped"] += 1
                        results["processed"] += 1
                    else:
                        results["skipped"] += 1
                        results["processed"] += 1
                        
                except Exception as e:
                    error_msg = f"Error processing character {character_file.name}: {str(e)}"
                    self.logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            self.logger.info(f"🎭 Characters synced: {results['processed']} processed")
            
        except Exception as e:
            error_msg = f"Error in character sync: {str(e)}"
            self.logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results
    
    def _sync_knowledge(self) -> Dict[str, Any]:
        """Sync knowledge files from vault to database"""
        results = {"processed": 0, "updated": 0, "skipped": 0, "errors": []}
        
        try:
            knowledge_path = self.vault_path / "knowledge"
            if not knowledge_path.exists():
                knowledge_path.mkdir(parents=True, exist_ok=True)
                self.logger.info("📚 Created knowledge directory")
                return results
            
            # Process subdirectories
            for category_dir in knowledge_path.iterdir():
                if category_dir.is_dir():
                    for knowledge_file in category_dir.glob("*.md"):
                        try:
                            if self._should_sync_file(knowledge_file):
                                success = self._process_knowledge_file(knowledge_file, category_dir.name)
                                if success:
                                    results["updated"] += 1
                                else:
                                    results["skipped"] += 1
                                results["processed"] += 1
                            else:
                                results["skipped"] += 1
                                results["processed"] += 1
                                
                        except Exception as e:
                            error_msg = f"Error processing knowledge {knowledge_file.name}: {str(e)}"
                            self.logger.error(error_msg)
                            results["errors"].append(error_msg)
            
            self.logger.info(f"📚 Knowledge synced: {results['processed']} processed")
            
        except Exception as e:
            error_msg = f"Error in knowledge sync: {str(e)}"
            self.logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results
    
    def _sync_templates(self) -> Dict[str, Any]:
        """Sync template files from vault to database"""
        results = {"processed": 0, "updated": 0, "skipped": 0, "errors": []}
        
        try:
            templates_path = self.vault_path / "templates"
            if not templates_path.exists():
                templates_path.mkdir(parents=True, exist_ok=True)
                self.logger.info("📝 Created templates directory")
                return results
            
            for template_file in templates_path.glob("*.md"):
                try:
                    if self._should_sync_file(template_file):
                        success = self._process_template_file(template_file)
                        if success:
                            results["updated"] += 1
                        else:
                            results["skipped"] += 1
                        results["processed"] += 1
                    else:
                        results["skipped"] += 1
                        results["processed"] += 1
                        
                except Exception as e:
                    error_msg = f"Error processing template {template_file.name}: {str(e)}"
                    self.logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            self.logger.info(f"📝 Templates synced: {results['processed']} processed")
            
        except Exception as e:
            error_msg = f"Error in template sync: {str(e)}"
            self.logger.error(error_msg)
            results["errors"].append(error_msg)
        
        return results
    
    def _should_sync_file(self, file_path: Path) -> bool:
        """Check if file should be synced based on modification time"""
        try:
            current_hash = self._get_file_hash(file_path)
            
            conn = sqlite3.connect(str(self.sync_db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT file_hash, last_modified FROM file_tracking WHERE file_path = ?
            ''', (str(file_path),))
            
            row = cursor.fetchone()
            conn.close()
            
            if row is None:
                # New file, should sync
                return True
            
            stored_hash, stored_modified = row
            file_modified = file_path.stat().st_mtime
            
            # Check if file has changed
            if current_hash != stored_hash:
                return True
            
            # Check if modification time has changed significantly
            if abs(file_modified - stored_modified) > 1:
                return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Hash check error for {file_path}: {e}")
            return True  # Sync if in doubt
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Get SHA256 hash of file content"""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            self.logger.error(f"Error hashing file {file_path}: {e}")
            return ""
    
    def _process_profile_file(self, file_path: Path) -> bool:
        """Process profile markdown file and update database"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Parse markdown content (simplified parser)
            profile_data = self._parse_markdown_profile(content)
            profile_data['id'] = file_path.stem  # Use filename without extension as ID
            
            # Update database (this would integrate with your existing profile manager)
            self._update_profile_in_db(profile_data)
            
            # Update tracking
            self._update_file_tracking(file_path, "profile")
            
            self.logger.info(f"✅ Processed profile: {file_path.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error processing profile {file_path.name}: {e}")
            return False
    
    def _process_character_file(self, file_path: Path) -> bool:
        """Process character markdown file and update database"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Parse markdown content
            character_data = self._parse_markdown_character(content)
            character_data['id'] = file_path.stem
            
            # Update database
            self._update_character_in_db(character_data)
            
            # Update tracking
            self._update_file_tracking(file_path, "character")
            
            self.logger.info(f"✅ Processed character: {file_path.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error processing character {file_path.name}: {e}")
            return False
    
    def _process_knowledge_file(self, file_path: Path, category: str) -> bool:
        """Process knowledge markdown file and update database"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Parse markdown content
            knowledge_data = {
                'title': file_path.stem,
                'content': content,
                'category': category,
                'tags': self._extract_tags_from_markdown(content),
                'last_modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
            }
            
            # Update database
            self._update_knowledge_in_db(knowledge_data)
            
            # Update tracking
            self._update_file_tracking(file_path, "knowledge")
            
            self.logger.info(f"✅ Processed knowledge: {file_path.name} [{category}]")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error processing knowledge {file_path.name}: {e}")
            return False
    
    def _process_template_file(self, file_path: Path) -> bool:
        """Process template markdown file and update database"""
        try:
            content = file_path.read_text(encoding='utf-8')
            
            # Parse markdown content
            template_data = {
                'name': file_path.stem,
                'content': content,
                'type': self._detect_template_type(content),
                'variables': self._extract_template_variables(content)
            }
            
            # Update database
            self._update_template_in_db(template_data)
            
            # Update tracking
            self._update_file_tracking(file_path, "template")
            
            self.logger.info(f"✅ Processed template: {file_path.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error processing template {file_path.name}: {e}")
            return False
    
    def _parse_markdown_profile(self, content: str) -> Dict[str, Any]:
        """Parse profile data from markdown content"""
        # Simple parser - in real implementation, you'd want a more robust markdown parser
        lines = content.split('\n')
        profile_data = {}
        
        current_section = None
        section_content = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('#'):
                if current_section and section_content:
                    profile_data[current_section] = '\n'.join(section_content).strip()
                current_section = line.lstrip('# ').lower().replace(' ', '_')
                section_content = []
            elif current_section and line:
                section_content.append(line)
        
        # Handle last section
        if current_section and section_content:
            profile_data[current_section] = '\n'.join(section_content).strip()
        
        # Extract metadata if present
        if 'metadata' in profile_data:
            try:
                # Try to parse YAML metadata
                import yaml
                metadata_lines = profile_data['metadata'].split('\n')
                metadata_content = '\n'.join(metadata_lines[1:-1])  # Remove --- lines
                profile_data['metadata_parsed'] = yaml.safe_load(metadata_content)
            except:
                pass
        
        return profile_data
    
    def _parse_markdown_character(self, content: str) -> Dict[str, Any]:
        """Parse character data from markdown content"""
        # Similar parsing logic to profile parser
        lines = content.split('\n')
        character_data = {}
        
        current_section = None
        section_content = []
        
        for line in lines:
            line = line.strip()
            if line.startswith('#'):
                if current_section and section_content:
                    character_data[current_section] = '\n'.join(section_content).strip()
                current_section = line.lstrip('# ').lower().replace(' ', '_')
                section_content = []
            elif current_section and line:
                section_content.append(line)
        
        if current_section and section_content:
            character_data[current_section] = '\n'.join(section_content).strip()
        
        return character_data
    
    def _extract_tags_from_markdown(self, content: str) -> List[str]:
        """Extract tags from markdown content"""
        import re
        # Find hashtags
        tags = re.findall(r'#(\w+)', content)
        return tags
    
    def _extract_template_variables(self, content: str) -> List[str]:
        """Extract template variables from content"""
        import re
        # Find {{variable}} patterns
        variables = re.findall(r'\{\{(\w+)\}\}', content)
        return list(set(variables))  # Remove duplicates
    
    def _detect_template_type(self, content: str) -> str:
        """Detect template type based on content"""
        content_lower = content.lower()
        if 'response' in content_lower or 'answer' in content_lower:
            return 'response'
        elif 'question' in content_lower or 'query' in content_lower:
            return 'question'
        elif 'greeting' in content_lower:
            return 'greeting'
        elif 'farewell' in content_lower:
            return 'farewell'
        else:
            return 'general'
    
    def _update_file_tracking(self, file_path: Path, file_type: str):
        """Update file tracking database"""
        try:
            file_hash = self._get_file_hash(file_path)
            
            conn = sqlite3.connect(str(self.sync_db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO file_tracking 
                (file_path, file_hash, last_modified, sync_status, last_sync, file_type)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                str(file_path),
                file_hash,
                file_path.stat().st_mtime,
                'synced',
                datetime.now().isoformat(),
                file_type
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error updating file tracking for {file_path}: {e}")
    
    def _update_sync_tracking(self):
        """Update sync operation tracking"""
        try:
            conn = sqlite3.connect(str(self.sync_db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sync_operations 
                (operation_type, timestamp, status, details)
                VALUES (?, ?, ?, ?)
            ''', (
                'full_sync',
                datetime.now().isoformat(),
                'completed',
                f'Synced at {datetime.now().isoformat()}'
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Error updating sync tracking: {e}")
    
    # Database update methods (these would integrate with your existing systems)
    def _update_profile_in_db(self, profile_data: Dict[str, Any]):
        """Update profile in main database"""
        # This would call your ProfileManager or similar
        self.logger.debug(f"Updating profile in DB: {profile_data.get('id', 'unknown')}")
    
    def _update_character_in_db(self, character_data: Dict[str, Any]):
        """Update character in main database"""
        # This would call your CharacterLoader or similar
        self.logger.debug(f"Updating character in DB: {character_data.get('id', 'unknown')}")
    
    def _update_knowledge_in_db(self, knowledge_data: Dict[str, Any]):
        """Update knowledge in main database"""
        # This would update your knowledge base
        self.logger.debug(f"Updating knowledge in DB: {knowledge_data.get('title', 'unknown')}")
    
    def _update_template_in_db(self, template_data: Dict[str, Any]):
        """Update template in main database"""
        # This would update your response templates
        self.logger.debug(f"Updating template in DB: {template_data.get('name', 'unknown')}")
    
    def get_sync_status(self) -> Dict[str, Any]:
        """Get current sync status"""
        try:
            conn = sqlite3.connect(str(self.sync_db_path))
            cursor = conn.cursor()
            
            # Get file tracking stats
            cursor.execute('SELECT COUNT(*), SUM(CASE WHEN sync_status = "synced" THEN 1 ELSE 0 END) FROM file_tracking')
            total_files, synced_files = cursor.fetchone()
            
            # Get last sync time
            cursor.execute('SELECT MAX(timestamp) FROM sync_operations WHERE status = "completed"')
            last_sync = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "status": "active" if self.file_observer else "inactive",
                "last_sync": last_sync,
                "total_files_tracked": total_files or 0,
                "files_synced": synced_files or 0,
                "files_pending": (total_files or 0) - (synced_files or 0),
                "auto_sync_enabled": self.sync_timer is not None,
                "file_watching_enabled": self.file_observer is not None
            }
            
        except Exception as e:
            self.logger.error(f"Error getting sync status: {e}")
            return {"status": "error", "error": str(e)}
    
    def force_sync(self) -> Dict[str, Any]:
        """Force immediate sync"""
        self.logger.info("⚡ Force sync initiated")
        return self.sync_vault_to_db()
    
    def get_tracked_files(self) -> List[Dict[str, Any]]:
        """Get list of tracked files"""
        try:
            conn = sqlite3.connect(str(self.sync_db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT file_path, file_type, last_modified, sync_status, last_sync
                FROM file_tracking
                ORDER BY last_modified DESC
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            files = []
            for row in rows:
                files.append({
                    'path': row[0],
                    'type': row[1],
                    'last_modified': row[2],
                    'sync_status': row[3],
                    'last_sync': row[4]
                })
            
            return files
            
        except Exception as e:
            self.logger.error(f"Error getting tracked files: {e}")
            return []

# Test function
def test_sync_service():
    """Test Sync Service functionality"""
    print("🔄 Testing Sync Service...")
    
    # Create sync service instance
    sync_service = SyncService("../obsidian_vault", "../databases/test_sync.db")
    
    # Test status
    print("\n📊 Testing sync status...")
    status = sync_service.get_sync_status()
    print(f"Sync status: {status}")
    
    # Test force sync
    print("\n⚡ Testing force sync...")
    sync_result = sync_service.force_sync()
    print(f"Sync result: {sync_result}")
    
    # Test tracked files
    print("\n📁 Testing tracked files...")
    tracked_files = sync_service.get_tracked_files()
    print(f"Tracked files: {len(tracked_files)} files")
    
    # Test sync service start/stop
    print("\n🚀 Testing service start/stop...")
    start_result = sync_service.start_sync_service(auto_sync=False, watch_files=False)
    print(f"Service start: {'✅ Success' if start_result else '❌ Failed'}")
    
    sync_service.stop_sync_service()
    print("Service stopped")
    
    print("\n✅ Sync Service test completed!")

if __name__ == "__main__":
    test_sync_service()
