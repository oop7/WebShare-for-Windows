"""
Pytest configuration and shared fixtures
"""

import pytest
import sys
import os

# Add app directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
