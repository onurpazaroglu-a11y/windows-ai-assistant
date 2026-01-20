#!/usr/bin/env python3
"""
Debug import issues
"""

import sys
import os

print("🔍 Debug Import Issues")
print("=" * 30)

# Current working directory
print(f"Current directory: {os.getcwd()}")

# Python path
print(f"Python path: {sys.path[:3]}...")  # İlk 3 path

# Try different import methods
print("\n🧪 Testing imports:")

# Method 1: Direct path
try:
    sys.path.insert(0, '/workspace/src/PythonBackend')
    from core.ai_engine import AICoreEngine
    print("✅ Method 1: Direct path import SUCCESS")
except Exception as e:
    print(f"❌ Method 1 failed: {e}")

# Method 2: Relative to current file
try:
    current_file = os.path.dirname(os.path.abspath(__file__))
    core_path = os.path.join(current_file, 'core')
    if os.path.exists(core_path):
        print(f"✅ Core path exists: {core_path}")
        sys.path.insert(0, current_file)
        from core.ai_engine import AICoreEngine
        print("✅ Method 2: Relative import SUCCESS")
    else:
        print(f"❌ Core path doesn't exist: {core_path}")
except Exception as e:
    print(f"❌ Method 2 failed: {e}")

# Method 3: List files
print(f"\n📁 Files in current directory:")
for item in os.listdir('.'):
    print(f"  - {item}")

print(f"\n📁 Files in core directory:")
if os.path.exists('core'):
    for item in os.listdir('core'):
        print(f"  - {item}")
else:
    print("  ❌ core directory not found")

print("\n✅ Debug complete")
