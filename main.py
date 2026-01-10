#!/usr/bin/env python3
"""
Alternative entry point for running the PicoBlog application.
"""

from app import app

def main():
    """Run the Flask application."""
    import os
    debug_mode = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    app.run(debug=debug_mode, host='127.0.0.1', port=5000)

if __name__ == "__main__":
    main()
