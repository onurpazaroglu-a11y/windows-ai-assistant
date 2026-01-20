class AIAssistantGUI {
    constructor() {
        this.apiUrl = '';
        this.currentProfile = 'personal';
        this.currentCharacter = 'artemis';
        this.isThinking = false;
        
        this.initializeElements();
        this.attachEventListeners();
        this.checkHealth();
        this.loadChatHistory();
    }
    
    initializeElements() {
        this.elements = {
            chatMessages: document.getElementById('chat-messages'),
            userInput: document.getElementById('user-input'),
            sendButton: document.getElementById('send-button'),
            voiceButton: document.getElementById('voice-button'),
            profileSelect: document.getElementById('profile-select'),
            characterSelect: document.getElementById('character-select'),
            syncNow: document.getElementById('sync-now'),
            clearChat: document.getElementById('clear-chat'),
            statusIndicator: document.getElementById('status-indicator'),
            profileDisplay: document.getElementById('profile-display')
        };
    }
    
    attachEventListeners() {
        // Mesaj gönderme
        this.elements.sendButton.addEventListener('click', () => this.sendMessage());
        this.elements.userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.sendMessage();
        });
        
        // Hızlı komutlar
        document.querySelectorAll('.quick-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.elements.userInput.value = btn.dataset.command;
                this.sendMessage();
            });
        });
        
        // Profil değişikliği
        this.elements.profileSelect.addEventListener('change', (e) => {
            this.switchProfile(e.target.value);
        });
        
        // Karakter değişikliği
        this.elements.characterSelect.addEventListener('change', (e) => {
            this.switchCharacter(e.target.value);
        });
        
        // Senkronizasyon
        this.elements.syncNow.addEventListener('click', () => this.syncNow());
        
        // Sohbet temizleme
        this.elements.clearChat.addEventListener('click', () => this.clearChat());
        
        // Ses butonu
        this.elements.voiceButton.addEventListener('click', () => this.toggleVoice());
    }
    
    async checkHealth() {
        try {
            const response = await fetch(this.apiUrl + '/ai/health');
            const data = await response.json();
            
            if (data.status === 'healthy') {
                this.elements.statusIndicator.textContent = '🟢 Online';
                this.elements.statusIndicator.className = 'status-online';
                this.updateProfileDisplay();
            } else {
                this.elements.statusIndicator.textContent = '🟡 Degraded';
                this.elements.statusIndicator.className = 'status-offline';
            }
        } catch (error) {
            this.elements.statusIndicator.textContent = '🔴 Offline';
            this.elements.statusIndicator.className = 'status-offline';
            console.error('Health check failed:', error);
        }
    }
    
    async sendMessage() {
        const message = this.elements.userInput.value.trim();
        if (!message || this.isThinking) return;
        
        // Kullanıcı mesajını göster
        this.addMessage(message, 'user');
        this.elements.userInput.value = '';
        
        // Düşünme animasyonu
        this.showThinking();
        
        try {
            const response = await fetch(this.apiUrl + '/ai/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: message })
            });
            
            const data = await response.json();
            
            // Düşünme animasyonunu kaldır
            this.hideThinking();
            
            if (data.response) {
                this.addMessage(data.response, 'bot');
            } else {
                this.addMessage('Üzgünüm, bir hata oluştu.', 'bot');
            }
            
            // Sohbet geçmişini kaydet
            this.saveChatHistory();
            
        } catch (error) {
            this.hideThinking();
            this.addMessage('Bağlantı hatası oluştu. Lütfen sunucunun çalıştığından emin olun.', 'bot');
            console.error('Send message error:', error);
        }
    }
    
    addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const now = new Date();
        const timeString = now.toLocaleTimeString('tr-TR', { 
            hour: '2-digit', 
            minute: '2-digit' 
        });
        
        messageDiv.innerHTML = `
            <div class="message-content">
                <strong>${sender === 'user' ? 'Siz' : 'AI Asistan'}:</strong>
                <p>${this.escapeHtml(text)}</p>
            </div>
            <div class="message-time">${timeString}</div>
        `;
        
        this.elements.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    showThinking() {
        this.isThinking = true;
        const thinkingDiv = document.createElement('div');
        thinkingDiv.className = 'message bot-message';
        thinkingDiv.id = 'thinking-message';
        thinkingDiv.innerHTML = `
            <div class="message-content">
                <strong>AI Asistan:</strong>
                <p class="thinking">
                    <span class="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                    </span>
                    Düşünüyor...
                </p>
            </div>
        `;
        this.elements.chatMessages.appendChild(thinkingDiv);
        this.scrollToBottom();
    }
    
    hideThinking() {
        this.isThinking = false;
        const thinkingMessage = document.getElementById('thinking-message');
        if (thinkingMessage) {
            thinkingMessage.remove();
        }
    }
    
    async switchProfile(profileId) {
        try {
            const response = await fetch(this.apiUrl + '/ai/profile/switch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ profile_id: profileId })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentProfile = profileId;
                this.updateProfileDisplay();
                this.addMessage(`Profil "${profileId}" olarak değiştirildi.`, 'bot');
                this.saveChatHistory();
            } else {
                this.addMessage('Profil değiştirme başarısız oldu.', 'bot');
            }
            
        } catch (error) {
            console.error('Profile switch error:', error);
            this.addMessage('Profil değiştirme sırasında hata oluştu.', 'bot');
        }
    }
    
    async switchCharacter(characterId) {
        try {
            const response = await fetch(this.apiUrl + '/ai/character/switch', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ character_id: characterId })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentCharacter = characterId;
                this.updateProfileDisplay();
                this.addMessage(`Karakter "${characterId}" olarak değiştirildi.`, 'bot');
                this.saveChatHistory();
            } else {
                this.addMessage('Karakter değiştirme başarısız oldu.', 'bot');
            }
            
        } catch (error) {
            console.error('Character switch error:', error);
            this.addMessage('Karakter değiştirme sırasında hata oluştu.', 'bot');
        }
    }
    
    updateProfileDisplay() {
        const profileNames = {
            'personal': 'Kişisel Asistan',
            'business': 'İş Asistanı',
            'education': 'Eğitim Asistanı'
        };
        
        const characterNames = {
            'artemis': 'Artemis',
            'corporate': 'Corporate Advisor',
            'study_buddy': 'Study Buddy'
        };
        
        this.elements.profileDisplay.textContent = 
            `Profil: ${profileNames[this.currentProfile] || this.currentProfile} | ` +
            `Karakter: ${characterNames[this.currentCharacter] || this.currentCharacter}`;
    }
    
    async syncNow() {
        try {
            this.addMessage('Senkronizasyon başlatılıyor...', 'bot');
            
            const response = await fetch(this.apiUrl + '/ai/sync/force', {
                method: 'POST'
            });
            
            const data = await response.json();
            
            if (data.status === 'success') {
                this.addMessage(`Senkronizasyon tamamlandı. ${data.processed_files} dosya işlendi.`, 'bot');
            } else {
                this.addMessage('Senkronizasyon sırasında bir hata oluştu.', 'bot');
            }
            
        } catch (error) {
            console.error('Sync error:', error);
            this.addMessage('Senkronizasyon hatası oluştu.', 'bot');
        }
    }
    
    clearChat() {
        if (confirm('Sohbet geçmişini temizlemek istediğinizden emin misiniz?')) {
            this.elements.chatMessages.innerHTML = '';
            localStorage.removeItem('ai_chat_history');
            this.addMessage('Sohbet geçmişi temizlendi.', 'bot');
        }
    }
    
    toggleVoice() {
        this.addMessage('Sesli komut özelliği henüz aktif değil.', 'bot');
    }
    
    scrollToBottom() {
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    saveChatHistory() {
        // Basit chat history kaydetme (isteğe bağlı genişletilebilir)
        const messages = Array.from(this.elements.chatMessages.children).map(msg => {
            return {
                html: msg.outerHTML,
                timestamp: new Date().toISOString()
            };
        });
        localStorage.setItem('ai_chat_history', JSON.stringify(messages));
    }
    
    loadChatHistory() {
        // Chat history yükleme (isteğe bağlı)
        const saved = localStorage.getItem('ai_chat_history');
        if (saved) {
            try {
                const messages = JSON.parse(saved);
                messages.forEach(msg => {
                    const tempDiv = document.createElement('div');
                    tempDiv.innerHTML = msg.html;
                    this.elements.chatMessages.appendChild(tempDiv.firstChild);
                });
                this.scrollToBottom();
            } catch (e) {
                console.error('Chat history load error:', e);
            }
        }
    }
}

// Uygulamayı başlat
document.addEventListener('DOMContentLoaded', () => {
    const gui = new AIAssistantGUI();
    
    // Otomatik sağlık kontrolü
    setInterval(() => gui.checkHealth(), 30000);
});
