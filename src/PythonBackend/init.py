"""
Windows AI Assistant Backend
"""
import os
import sys

# Add src to path
src_path = os.path.dirname(os.path.abspath(__file__))
if src_path not in sys.path:
    sys.path.insert(0, src_path)
