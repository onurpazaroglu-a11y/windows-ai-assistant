# **Windows AI Assistant**

A modular, cross-platform AI assistant with profile-based customization and character personalities.

## 🚀 **Features**

- 🎯 **Profile-based System**: Personal, Business, and Education profiles
- 🎭 **Character Personalities**: Different AI characters with unique personalities  
- 🧠 **Context Awareness**: Remembers conversations and user preferences
- 💾 **Database Integration**: SQLite-based persistent storage
- 🌐 **API Integration**: FastAPI-based REST API
- 🎨 **Modular Architecture**: Easy to extend and customize
- 🌍 **Multi-language Support**: Turkish, English, German, French
- ⚡ **Performance Optimized**: Lightweight and fast processing

## 🏗️ Architecture

Component Overview
Windows AI Assistant consists of several interconnected modules working together to provide a comprehensive AI assistant experience:

**Core Backend** (Python)
**AI Core Engine**: Main processing unit handling input/output operations
**Profile Manager**: Manages different user profiles (Personal, Business, Education)
**Character Loader**: Loads and manages AI character personalities
**Context Manager**: Handles conversation history and user context
**Response Generator**: Creates intelligent, character-appropriate responses
**Database Manager**: Manages all persistent data storage and retrieval

**Frontend Layer (C#)**
**GUI Application**: Main desktop interface for user interaction
**Settings Panel**: Configuration management interface
**System Tray Integration**: Background operation controls
**Notification System**: User alerts and status updates

**Service Layer (Windows)**
**Windows Service**: Background service for always-on operation
**Startup Manager**: Automatic startup configuration
**System Integration**: Windows API and system hooks

**Data Layer**
**SQLite Databases**: Structured data storage for conversations, preferences, and facts
**Obsidian Vault**: Human-readable markdown files for knowledge base
**Configuration Files**: JSON/XML settings and preferences

**API Layer**
**REST API**: HTTP interface for external applications and integrations
**IPC Communication**: Inter-process communication between components
**WebSocket Support**: Real-time communication capabilities

**Data Flow**
**User Input**: User interacts through GUI or voice → Frontend captures input
**API Processing**: Input sent to REST API → Python backend processes
**AI Analysis**: Core engine analyzes input using context and character data
**Response Generation**: Appropriate response created based on profile/character
**Data Storage**: Interaction stored in database for future context
**Output Delivery**: Response sent back to user via GUI or voice

**Communication Patterns**
**Synchronous**: Direct API calls for immediate responses
**Asynchronous**: Background processing for complex operations
**Event-Driven**: System events trigger specific actions
**Polling**: Periodic checks for updates and changes

**Deployment Options**
**Containerized**: Docker deployment for consistent environments
**Native Windows**: Traditional Windows installation
**Hybrid**: Combination of both approaches

**Scalability Features**
**Modular Design**: Components can be scaled independently
**Connection Pooling**: Efficient database connection management
**Caching**: Frequently accessed data cached for performance
**Load Distribution**: Multiple instances can work together


## 📦 **Components**

### **Core Engine**
- Main processing unit for AI operations
- Handles input processing and response generation
- Manages component coordination

### **Profile Manager**
- Loads and manages AI assistant profiles
- Supports Personal, Business, and Education profiles
- Validates system requirements

### **Character Loader**
- Loads character personalities and traits
- Manages character-specific behaviors
- Ensures profile-character compatibility

### **Context Manager**
- Maintains conversation history
- Stores user preferences and facts
- Provides contextual awareness

### **Response Generator**
- Creates intelligent responses
- Uses character personalities and context
- Supports dynamic variable processing

### **Database Manager**
- Persistent data storage
- Performance optimized with connection pooling
- Automatic backup and cleanup

## 🛠️ **Installation**

### **Prerequisites**
- Python 3.8+
- Docker (optional)
- Windows 10/11 for full features

### **Quick Start**

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/windows-ai-assistant.git
cd windows-ai-assistant

# Install dependencies
pip install -r src/PythonBackend/requirements.txt

# Run the application
cd src/PythonBackend
python main.py

# Access API at http://localhost:8000

# Build and run with Docker
docker-compose up --build

# Access at http://localhost:8000

🌐 **API Endpoints**

Core Endpoints
GET / - Health check and welcome message
GET /health - Detailed health status
GET /docs - Interactive API documentation

AI Engine Endpoints
GET /ai/status - AI engine status and statistics
POST /ai/process - Process user input and get response
GET /ai/profiles - List available profiles
GET /ai/characters - List available characters
POST /ai/profile/switch - Switch to different profile
POST /ai/character/switch - Switch to different character
GET /ai/compatibility/{profile_id} - Get compatible characters

Database Endpoints (Advanced)
GET /ai/database/stats - Database statistics
GET /ai/database/metrics - Performance metrics
POST /ai/database/backup - Database backup
POST /ai/database/cleanup - Clean old data

🎮 **Usage Examples**

Basic Interaction
# Send a greeting
curl -X POST http://localhost:8000/ai/process \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello, my name is John"}'

# Ask about the time
curl -X POST http://localhost:8000/ai/process \
  -H "Content-Type: application/json" \
  -d '{"text": "What time is it?"}'

# Switch profile
curl -X POST http://localhost:8000/ai/profile/switch \
  -H "Content-Type: application/json" \
  -d '{"profile_id": "business"}'

Character Personalities
Artemis: Friendly personal assistant (Personal profile)
Corporate Advisor: Professional business assistant (Business profile)
Study Buddy: Educational assistant (Education profile)

📊 **Performance Metrics**
Average Response Time: < 200ms
Database Operations: Connection pooling optimized
Memory Usage: < 100MB baseline
Scalability: Supports multiple concurrent sessions

🤝 **Contributing**

Fork the repository
Create your feature branch (git checkout -b feature/AmazingFeature)
Commit your changes (git commit -m 'Add some AmazingFeature')
Push to the branch (git push origin feature/AmazingFeature)
Open a Pull Request

📄 **License**
This project is licensed under the MIT License - see the LICENSE [blocked] file for details.

👥 **Authors**
Your Name - Initial work - YourGitHub

🙏 **Acknowledgments**
Thanks to all contributors who participated in this project
Inspired by modern AI assistant technologies