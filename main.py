"""
Application entry point.
Uses app factory pattern for better structure.
"""

from dotenv import load_dotenv
load_dotenv()

from app import create_app
import os

# Create app instance
app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
