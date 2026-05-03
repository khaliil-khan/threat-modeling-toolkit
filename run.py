from app import create_app, db
import os

app = create_app()

if __name__ == '__main__':
    # Initialize database
    with app.app_context():
        db.create_all()
        print('✓ Database initialized')
    
    debug_mode = os.environ.get('FLASK_DEBUG', '').lower() in ('1', 'true', 'yes')
    port = int(os.environ.get('PORT', 5000))
    
    print(f'✓ Starting Flask app in {"debug" if debug_mode else "production"} mode')
    print(f'✓ Database: {app.config.get("SQLALCHEMY_DATABASE_URI")}')
    
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
