#!/usr/bin/env python3
"""
New Flask application entry point using refactored architecture.
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.api.web_app import create_app
from src.config.settings import get_settings

def main():
    """Main application entry point."""
    app = create_app()
    settings = get_settings()
    
    app.run(
        host=settings.server.host,
        port=settings.server.port,
        debug=settings.server.debug
    )

if __name__ == '__main__':
    main()
