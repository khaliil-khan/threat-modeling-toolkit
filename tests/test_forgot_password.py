"""Unit tests for forgot_password route behavior.

Tests verify that the forgot_password route always shows the same generic
flash message regardless of the return value from send_reset_email, ensuring
no information leakage about email existence or delivery status.

Validates: Requirements 2.4
"""

import os
from unittest.mock import patch, MagicMock

import pytest
from flask import Flask
from flask_login import LoginManager

from app.models import db, User


def _create_test_app():
    """Create a minimal Flask app with the auth blueprint for testing."""
    from flask_wtf import CSRFProtect

    app = Flask(__name__, template_folder='../app/templates')
    app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,
        'SERVER_NAME': 'localhost',
    })

    db.init_app(app)
    CSRFProtect(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    from app.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    with app.app_context():
        db.create_all()

    return app


@pytest.fixture
def app():
    """Create a Flask application configured for testing."""
    test_app = _create_test_app()
    with test_app.app_context():
        yield test_app


@pytest.fixture
def client(app):
    """Create a Flask test client."""
    return app.test_client()


@pytest.fixture(autouse=True)
def clear_rate_limits():
    """Clear rate limit stores between tests to prevent interference."""
    from app.auth.routes import _reset_attempts
    _reset_attempts.clear()
    yield
    _reset_attempts.clear()


@pytest.fixture
def test_user(app):
    """Create a test user in the database."""
    user = User(username='testuser', email='testuser@example.com', role='user')
    user.set_password('SecurePass123!')
    db.session.add(user)
    db.session.commit()
    return user


GENERIC_MESSAGE = "If that email is registered, you will receive reset instructions shortly."


def _get_flashed_messages(client, response):
    """Extract flashed messages from the session cookie after a response."""
    with client.session_transaction() as sess:
        flashes = sess.get('_flashes', [])
        return [msg for _category, msg in flashes]


class TestForgotPasswordGenericMessage:
    """Tests that the forgot_password route always shows the same generic
    flash message regardless of send_reset_email return value (no leak)."""

    def test_generic_message_when_send_reset_email_returns_true(self, client, test_user):
        """When send_reset_email returns True (email sent successfully),
        the generic message is shown."""
        with patch('app.auth.routes.send_reset_email', return_value=True) as mock_send:
            response = client.post(
                '/auth/forgot-password',
                data={'email': 'testuser@example.com'},
                follow_redirects=False,
            )

            assert response.status_code == 302
            messages = _get_flashed_messages(client, response)
            assert GENERIC_MESSAGE in messages
            mock_send.assert_called_once()

    def test_generic_message_when_send_reset_email_returns_logged(self, client, test_user):
        """When send_reset_email returns 'logged' (SMTP unconfigured, URL logged),
        the generic message is shown."""
        with patch('app.auth.routes.send_reset_email', return_value='logged') as mock_send:
            response = client.post(
                '/auth/forgot-password',
                data={'email': 'testuser@example.com'},
                follow_redirects=False,
            )

            assert response.status_code == 302
            messages = _get_flashed_messages(client, response)
            assert GENERIC_MESSAGE in messages
            mock_send.assert_called_once()

    def test_generic_message_when_send_reset_email_returns_false(self, client, test_user):
        """When send_reset_email returns False (email delivery failed),
        the generic message is shown without revealing delivery status (no leak)."""
        with patch('app.auth.routes.send_reset_email', return_value=False) as mock_send:
            response = client.post(
                '/auth/forgot-password',
                data={'email': 'testuser@example.com'},
                follow_redirects=False,
            )

            assert response.status_code == 302
            messages = _get_flashed_messages(client, response)
            assert GENERIC_MESSAGE in messages
            # Ensure no error-specific message is leaked to the user
            for msg in messages:
                assert 'Email delivery failed' not in msg
            mock_send.assert_called_once()

    def test_generic_message_for_nonexistent_email(self, client, test_user):
        """When the email does not exist in the database, the same generic
        message is shown (no user enumeration)."""
        with patch('app.auth.routes.send_reset_email') as mock_send:
            response = client.post(
                '/auth/forgot-password',
                data={'email': 'nonexistent@example.com'},
                follow_redirects=False,
            )

            assert response.status_code == 302
            messages = _get_flashed_messages(client, response)
            assert GENERIC_MESSAGE in messages
            # send_reset_email should NOT be called for non-existent users
            mock_send.assert_not_called()
