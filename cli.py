#!/usr/bin/env python3
"""
New CLI application entry point using refactored architecture.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.api.cli_app import main

if __name__ == '__main__':
    main()
