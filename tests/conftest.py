"""Shared test fixtures for the Threat Toolkit test suite."""

import pytest
from app import create_app


@pytest.fixture
def app():
    """Create a Flask application configured for testing."""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
    })
    yield app


@pytest.fixture
def client(app):
    """Create a Flask test client."""
    return app.test_client()
