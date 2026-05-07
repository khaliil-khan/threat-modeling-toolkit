"""Property-based tests for email console fallback behavior.

Tests verify that when SMTP environment variables are absent, the
send_reset_email function logs the username and reset URL at INFO level
and returns the distinct status string 'logged'.

Validates: Requirements 1.1, 1.2, 1.3
"""

import logging
import logging.handlers
import os
from unittest.mock import patch, MagicMock

import pytest
from flask import Flask
from hypothesis import given, settings
from hypothesis import strategies as st

from app.auth.routes import send_reset_email


# Strategy for generating valid usernames (non-empty, printable, no whitespace-only)
username_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P'), whitelist_characters='_-'),
    min_size=1,
    max_size=80,
).filter(lambda s: s.strip() != '')

# Strategy for generating reset tokens (URL-safe base64-like strings, ASCII only)
# Real tokens from URLSafeTimedSerializer are always ASCII URL-safe characters
token_strategy = st.text(
    alphabet=st.sampled_from(
        'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.'
    ),
    min_size=10,
    max_size=200,
)


def _make_mock_user(username, email=None):
    """Create a mock User object with the given username."""
    user = MagicMock()
    user.username = username
    user.email = email or f'{username}@example.com'
    return user


def _create_minimal_app():
    """Create a minimal Flask app with just the auth blueprint for testing."""
    app = Flask(__name__)
    app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
        'SERVER_NAME': 'localhost',
    })

    # Register the auth blueprint so url_for('auth.reset_password', ...) works
    from app.auth import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    return app


class TestConsoleFallbackLogsUsernameAndResetURL:
    """Property 1: Console fallback logs username and reset URL.

    For any valid User object and any generated reset token, when SMTP
    environment variables are all absent, calling send_reset_email(user, token)
    SHALL produce a log message at INFO level that contains both the user's
    username and the full reset URL.

    **Validates: Requirements 1.1, 1.2**
    """

    @settings(max_examples=100)
    @given(username=username_strategy, token=token_strategy)
    def test_console_fallback_logs_username_and_url(self, username, token):
        """For any valid user and token, when SMTP is absent, the log SHALL
        contain both the username and the reset URL."""
        app = _create_minimal_app()

        mock_user = _make_mock_user(username)

        # Clear all SMTP environment variables
        env_overrides = {
            'SMTP_SERVER': '',
            'SENDER_EMAIL': '',
            'SENDER_PASSWORD': '',
        }

        with app.app_context():
            with patch.dict(os.environ, env_overrides, clear=False):
                with app.test_request_context('/'):
                    # Use a log handler to capture INFO messages from the app logger
                    handler = logging.handlers.MemoryHandler(capacity=100)
                    handler.setLevel(logging.INFO)
                    # Store records directly
                    captured_records = []

                    class RecordCapture(logging.Handler):
                        def emit(self, record):
                            captured_records.append(record)

                    capture_handler = RecordCapture()
                    capture_handler.setLevel(logging.INFO)
                    app.logger.addHandler(capture_handler)
                    app.logger.setLevel(logging.INFO)

                    try:
                        result = send_reset_email(mock_user, token)
                    finally:
                        app.logger.removeHandler(capture_handler)

                    # Filter for INFO level records
                    info_records = [r for r in captured_records if r.levelno == logging.INFO]

                    # Verify at least one INFO log was produced
                    assert len(info_records) > 0, (
                        "Expected at least one INFO log when SMTP is not configured"
                    )

                    # Format all INFO log messages
                    log_messages = [r.getMessage() for r in info_records]
                    combined_log = ' '.join(log_messages)

                    # The log must contain the username
                    assert username in combined_log, (
                        f"Username '{username}' not found in log messages: {log_messages}"
                    )

                    # The log must contain the reset URL (which includes the token)
                    assert token in combined_log, (
                        f"Token '{token}' not found in log messages: {log_messages}"
                    )


class TestConsoleFallbackReturnsDistinctStatus:
    """Property 2: Console fallback returns distinct status.

    For any valid User object and any generated reset token, when SMTP
    environment variables are all absent, calling send_reset_email(user, token)
    SHALL return the string 'logged' (not True and not False).

    **Validates: Requirements 1.3**
    """

    @settings(max_examples=100)
    @given(username=username_strategy, token=token_strategy)
    def test_console_fallback_returns_logged_string(self, username, token):
        """For any valid user and token, when SMTP is absent, the return value
        SHALL be the string 'logged'."""
        app = _create_minimal_app()

        mock_user = _make_mock_user(username)

        # Clear all SMTP environment variables
        env_overrides = {
            'SMTP_SERVER': '',
            'SENDER_EMAIL': '',
            'SENDER_PASSWORD': '',
        }

        with app.app_context():
            with patch.dict(os.environ, env_overrides, clear=False):
                with app.test_request_context('/'):
                    result = send_reset_email(mock_user, token)

        # Return value must be exactly the string 'logged'
        assert result == 'logged', (
            f"Expected return value 'logged', got {result!r}"
        )

        # It must not be True or False (distinct from boolean returns)
        assert result is not True, (
            "Return value should be the string 'logged', not True"
        )
        assert result is not False, (
            "Return value should be the string 'logged', not False"
        )

        # Verify it's actually a string type
        assert isinstance(result, str), (
            f"Return value should be a string, got {type(result).__name__}"
        )
