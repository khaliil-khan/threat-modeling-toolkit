"""
WSGI entry point for production deployment.
Used by gunicorn: gunicorn wsgi:app
"""
from app import create_app, db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    app = create_app()
    logger.info('Flask app created successfully')
except Exception as e:
    logger.error('Failed to create Flask app: %s', str(e), exc_info=True)
    raise

# Initialize database on startup
try:
    with app.app_context():
        db.create_all()
        logger.info('Database initialized')
except Exception as e:
    logger.error('Failed to initialize database: %s', str(e), exc_info=True)
    raise

if __name__ == '__main__':
    # Only for local development fallback — production uses gunicorn
    app.run(host='0.0.0.0', port=5000, debug=False)
