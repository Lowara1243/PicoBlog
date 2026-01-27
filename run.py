#!/usr/bin/env python3
"""
Entry point for running the PicoBlog application in development mode.
For production, use a WSGI server like Gunicorn or uWSGI.
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Run in development mode
    # Note: Set debug=False in production
    import os

    debug_mode = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    app.run(debug=debug_mode, host="127.0.0.1", port=5000)
