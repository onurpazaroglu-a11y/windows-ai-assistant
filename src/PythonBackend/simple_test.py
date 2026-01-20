#!/usr/bin/env python3
"""
Basit AI Test - Modül sorunlarını çözmek için
"""

import sys
import os
from datetime import datetime

# Basit AI motoru
class SimpleAI:
    def process_input(self, text):
        text_lower = text.lower()
        if "merhaba" in text_lower:
            return "Merhaba! Size nasıl yardımcı olabilirim?"
        elif "saat" in text_lower:
            return f"Şu anda saat: {datetime.now().strftime('%H:%M:%S')}"
        elif "yardım" in text_lower:
            return "Yardım için: merhaba, saat, yardım komutlarını deneyin"
        else:
            return "Anlamadım. 'yardım' yazarak neler yapabileceğimi öğrenin."

# Test fonksiyonu
def test_ai():
    ai = SimpleAI()
    test_cases = ["Merhaba", "Saat kaç?", "Yardım et", "Nasıl gidiyor?"]
    
    print("🤖 AI Assistant Test")
    print("=" * 30)
    
    for case in test_cases:
        result = ai.process_input(case)
        print(f"Girdi: {case}")
        print(f"Yanıt: {result}")
        print("-" * 30)

if __name__ == "__main__":
    test_ai()
