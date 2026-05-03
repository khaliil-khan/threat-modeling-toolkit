"""
WSGI entry point for production deployment (container)
Initializes database and runs gunicorn
"""
from app import create_app, db
import os
import logging

# Enable detailed logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    app = create_app()
    logger.info('✓ Flask app created successfully')
except Exception as e:
    logger.error(f'✗ Failed to create Flask app: {str(e)}', exc_info=True)
    raise

# Initialize database on startup
try:
    with app.app_context():
        db.create_all()
        print('✓ Database initialized')
        logger.info('✓ Database initialized')
except Exception as e:
    logger.error(f'✗ Failed to initialize database: {str(e)}', exc_info=True)
    raise

if __name__ == '__main__':
    try:
        # For development with: gunicorn wsgi:app
        print('✓ Starting Flask app')
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        logger.error(f'✗ Failed to start Flask app: {str(e)}', exc_info=True)
        raise
