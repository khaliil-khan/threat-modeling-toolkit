from flask import Flask
from flask_login import LoginManager
from .models import db, User
import os
from datetime import timedelta
from flask_wtf import CSRFProtect
import logging

login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app_env = os.environ.get('APP_ENV', 'development').lower()
    is_production = app_env == 'production'
    is_debug = os.environ.get('FLASK_DEBUG', '').lower() in ('1', 'true', 'yes')

    secret_key = os.environ.get('SECRET_KEY')
    if is_production and not secret_key:
        raise RuntimeError('SECRET_KEY must be set in production.')

    app.config['SECRET_KEY'] = secret_key or 'dev-secret-change-in-prod'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///threats.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['REMEMBER_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
    app.config['SESSION_COOKIE_SECURE'] = is_production
    app.config['REMEMBER_COOKIE_SECURE'] = is_production
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
    
    # Setup logging
    if not app.debug:
        if is_debug:
            app.logger.setLevel(logging.DEBUG)
        else:
            app.logger.setLevel(logging.INFO)

    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'
    login_manager.session_protection = 'strong'

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    @app.context_processor
    def template_helpers():
        def endpoint_exists(endpoint):
            return endpoint in app.view_functions

        return {'endpoint_exists': endpoint_exists}

    @app.errorhandler(500)
    def handle_500_error(error):
        app.logger.error(f'500 Error: {str(error)}', exc_info=error)
        return {'error': 'Internal Server Error', 'message': str(error)}, 500

    @app.errorhandler(404)
    def handle_404_error(error):
        app.logger.warning(f'404 Error: {str(error)}')
        return {'error': 'Not Found', 'message': str(error)}, 404

    @app.after_request
    def add_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        csp = "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; img-src 'self' data:; object-src 'none'; base-uri 'self'; frame-ancestors 'self'"
        response.headers['Content-Security-Policy'] = csp
        return response

    from .auth import auth_bp
    from .threats import threats_bp
    from .dashboard import dashboard_bp
    from .reports import reports_bp
    from .dfd import dfd_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(threats_bp, url_prefix='/threats')
    app.register_blueprint(dashboard_bp, url_prefix='/')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(dfd_bp, url_prefix='/dfd')

    with app.app_context():
        db.create_all()

    return app
