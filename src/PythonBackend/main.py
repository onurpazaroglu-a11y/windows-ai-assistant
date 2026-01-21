#!/usr/bin/env python3
"""
Windows AI Assistant - Python Backend with Web GUI
"""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI(title="Windows AI Assistant")

# Basit HTML içeriği
HTML_CONTENT = '''<!DOCTYPE html>
<html>
<head>
    <title>Windows AI Assistant</title>
    <meta charset="utf-8">
    <style>
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }
        h1 { 
            color: #333; 
            text-align: center; 
            margin-bottom: 30px;
        }
        .chat-box {
            background: #f8f9fa;
            color: #333;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            height: 400px;
            overflow-y: scroll;
            border: 1px solid #ddd;
        }
        .input-area {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        input[type="text"] {
            flex: 1;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 25px;
            font-size: 16px;
        }
        button {
            padding: 12px 25px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background: #45a049;
        }
        .message {
            margin: 10px 0;
            padding: 10px;
            border-radius: 8px;
        }
        .user-message {
            background: #2196F3;
            color: white;
            text-align: right;
        }
        .bot-message {
            background: #e9ecef;
            color: #333;
        }
        .controls {
            display: flex;
            gap: 10px;
            margin: 20px 0;
            flex-wrap: wrap;
        }
        .control-btn {
            padding: 8px 15px;
            background: #ff9800;
            color: white;
            border: none;
            border-radius: 15px;
            cursor: pointer;
        }
        .control-btn:hover {
            background: #e68a00;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Windows AI Assistant</h1>
        
        <div class="controls">
            <button class="control-btn" onclick="switchProfile('personal')">👤 Kişisel</button>
            <button class="control-btn" onclick="switchProfile('business')">💼 İş</button>
            <button class="control-btn" onclick="switchProfile('education')">🎓 Eğitim</button>
            <button class="control-btn" onclick="switchCharacter('artemis')">👩 Artemis</button>
            <button class="control-btn" onclick="switchCharacter('corporate')">👔 Corporate</button>
            <button class="control-btn" onclick="getStatus()">📊 Durum</button>
        </div>

        <div class="chat-box" id="chatBox">
            <div class="message bot-message">
                <strong>AI Asistan:</strong>
                <p>Merhaba! Size nasıl yardımcı olabilirim?</p>
            </div>
        </div>

        <div class="input-area">
            <input type="text" id="userInput" placeholder="Mesajınızı yazın..." onkeypress="if(event.keyCode==13) sendMessage()">
            <button onclick="sendMessage()">Gönder</button>
        </div>
    </div>

    <script>
        function sendMessage() {
            const input = document.getElementById('userInput');
            const message = input.value.trim();
            if (!message) return;

            // Kullanıcı mesajını göster
            addMessage(message, 'user');
            input.value = '';

            // API'ye istek gönder
            fetch('/api/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({text: message})
            })
            .then(response => response.json())
            .then(data => {
                addMessage(data.response || 'Yanıt alınamadı', 'bot');
            })
            .catch(error => {
                addMessage('Hata oluştu: ' + error, 'bot');
            });
        }

        function addMessage(text, sender) {
            const chatBox = document.getElementById('chatBox');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${sender}-message`;
            messageDiv.innerHTML = `<strong>${sender === 'user' ? 'Siz' : 'AI Asistan'}:</strong><p>${text}</p>`;
            chatBox.appendChild(messageDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
        }

        function switchProfile(profile) {
            fetch('/api/profile/switch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({profile_id: profile})
            })
            .then(response => response.json())
            .then(data => {
                addMessage(`Profil ${profile} olarak değiştirildi`, 'bot');
            });
        }

        function switchCharacter(character) {
            fetch('/api/character/switch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({character_id: character})
            })
            .then(response => response.json())
            .then(data => {
                addMessage(`Karakter ${character} olarak değiştirildi`, 'bot');
            });
        }

        function getStatus() {
            fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                addMessage(`Durum: ${JSON.stringify(data)}`, 'bot');
            });
        }
    </script>
</body>
</html>'''

@app.get("/", response_class=HTMLResponse)
async def read_root():
    return HTML_CONTENT

# API endpoint'leri
@app.get("/api/info")
async def api_info():
    return {"message": "Windows AI Assistant API", "status": "running"}

@app.post("/api/process")
async def process_input(input_data: dict):
    text = input_data.get("text", "")
    if "merhaba" in text.lower():
        response = "Merhaba! Size nasıl yardımcı olabilirim?"
    elif "saat" in text.lower():
        from datetime import datetime
        response = f"Şu anda saat: {datetime.now().strftime('%H:%M:%S')}"
    elif "yardım" in text.lower():
        response = "Yardım için şu komutları deneyebilirsiniz: merhaba, saat, yardım"
    else:
        response = "Anlayamadım. 'yardım' yazarak neler yapabileceğimi öğrenin."
    
    return {"response": response, "confidence": 0.8}

@app.get("/api/status")
async def get_status():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "components": ["AI Engine", "Profile Manager", "Character Loader"]
    }

@app.post("/api/profile/switch")
async def switch_profile(profile_data: dict):
    profile_id = profile_data.get("profile_id", "personal")
    return {"message": f"Profil {profile_id} olarak değiştirildi", "success": True}

@app.post("/api/character/switch")
async def switch_character(character_data: dict):
    character_id = character_data.get("character_id", "artemis")
    return {"message": f"Karakter {character_id} olarak değiştirildi", "success": True}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AI Assistant Backend"}

if __name__ == "__main__":
    print("🚀 Starting Windows AI Assistant...")
    print("🌐 Access GUI at: http://localhost:8000")
    print("📄 API Docs at: http://localhost:8000/docs")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
