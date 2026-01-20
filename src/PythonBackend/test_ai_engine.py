#!/usr/bin/env python3
"""
Test script for AI Core Engine
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.ai_engine import AICoreEngine
import json

def test_ai_engine():
    """
    Test the AI Core Engine functionality
"""
    print("🧪 Testing AI Core Engine...")
    
    # Create engine instance
    engine = AICoreEngine()
    
    # Initialize
    print("🔄 Initializing AI Engine...")
    success = engine.initialize()
    print(f"Initialization: {'✅ Success' if success else '❌ Failed'}")
    
    # Test inputs
    test_cases = [
        "Merhaba, nasılsın?",
        "Bugün saat kaç?",
        "Yardım eder misin?",
        "Görüşürüz, hoşça kal"
    ]
    
    print("\n💬 Processing test inputs:")
    for i, test_input in enumerate(test_cases, 1):
        print(f"\nTest {i}: '{test_input}'")
        result = engine.process_input(test_input)
        print(f"Response: {result.get('response', 'No response')}")
        print(f"Confidence: {result.get('confidence', 0):.2f}")
        print(f"Primary Intent: {result.get('intent', {}).get('primary', 'None')}")
    
    # Status check
    print(f"\n📊 Engine Status:")
    status = engine.get_status()
    print(json.dumps(status, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_ai_engine()
