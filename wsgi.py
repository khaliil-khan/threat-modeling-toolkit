"""
WSGI entry point for production deployment (container)
Initializes database and runs gunicorn
"""
from app import create_app, db
import os

app = create_app()

# Initialize database on startup
with app.app_context():
    db.create_all()
    print('✓ Database initialized')

if __name__ == '__main__':
    # For development with: gunicorn wsgi:app
    app.run(host='0.0.0.0', port=5000)
