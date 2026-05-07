"""Property-based tests for CSP nonce generation.

Tests verify that the CSP nonce infrastructure generates unique nonces per
request and correctly embeds them in the Content-Security-Policy header.

Validates: Requirements 4.1, 4.2
"""

import re

import pytest
from hypothesis import given, settings, assume
from hypothesis import strategies as st

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


class TestCSPNonceUniqueness:
    """Property 3: CSP nonce uniqueness.

    For any two distinct HTTP requests to the application, the CSP nonces
    generated for each request SHALL be different strings.

    **Validates: Requirements 4.1**
    """

    @settings(max_examples=100)
    @given(num_requests=st.integers(min_value=2, max_value=20))
    def test_nonces_are_unique_across_multiple_requests(self, num_requests):
        """For any N distinct HTTP requests, all CSP nonces SHALL be unique."""
        app = create_app()
        app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False,
        })

        nonces = []
        with app.test_client() as client:
            for _ in range(num_requests):
                response = client.get('/')
                csp_header = response.headers.get('Content-Security-Policy', '')
                # Extract nonce from script-src directive
                match = re.search(r"'nonce-([^']+)'", csp_header)
                assert match is not None, (
                    f"CSP header missing nonce. Header: {csp_header}"
                )
                nonces.append(match.group(1))

        # All nonces must be unique
        assert len(nonces) == len(set(nonces)), (
            f"Duplicate nonces found among {num_requests} requests. "
            f"Nonces: {nonces}"
        )


class TestCSPHeaderContainsNonce:
    """Property 4: CSP header contains generated nonce.

    For any HTTP response from the application, the Content-Security-Policy
    header's script-src directive SHALL contain the string 'nonce-<N>' where
    <N> is the nonce generated for that request.

    **Validates: Requirements 4.2**
    """

    @settings(max_examples=100)
    @given(request_path=st.sampled_from(['/', '/auth/login', '/auth/register']))
    def test_csp_header_contains_nonce_in_script_src(self, request_path):
        """For any HTTP response, the CSP script-src SHALL contain the nonce."""
        app = create_app()
        app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False,
        })

        with app.test_client() as client:
            response = client.get(request_path)
            csp_header = response.headers.get('Content-Security-Policy', '')

            # CSP header must exist
            assert csp_header, (
                f"No Content-Security-Policy header on response to {request_path}"
            )

            # script-src directive must exist
            assert 'script-src' in csp_header, (
                f"No script-src directive in CSP header: {csp_header}"
            )

            # Extract the nonce value from the CSP header
            nonce_match = re.search(r"'nonce-([^']+)'", csp_header)
            assert nonce_match is not None, (
                f"No nonce found in CSP header script-src. Header: {csp_header}"
            )

            nonce_value = nonce_match.group(1)

            # Nonce must be non-empty
            assert len(nonce_value) > 0, "CSP nonce is empty"

            # Nonce must be a valid base64url string (from secrets.token_urlsafe)
            assert re.match(r'^[A-Za-z0-9_-]+$', nonce_value), (
                f"Nonce is not a valid base64url string: {nonce_value}"
            )

            # The full nonce directive must be properly formatted
            expected_nonce_directive = f"'nonce-{nonce_value}'"
            assert expected_nonce_directive in csp_header, (
                f"Expected {expected_nonce_directive} in CSP header. "
                f"Header: {csp_header}"
            )

    @settings(max_examples=100)
    @given(data=st.data())
    def test_nonce_in_header_matches_request_context(self, data):
        """The nonce in the CSP header SHALL match the nonce generated for that request."""
        app = create_app()
        app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'WTF_CSRF_ENABLED': False,
        })

        with app.test_client() as client:
            response = client.get('/')
            csp_header = response.headers.get('Content-Security-Policy', '')

            # Extract nonce from CSP header
            nonce_match = re.search(r"'nonce-([^']+)'", csp_header)
            assert nonce_match is not None, (
                f"No nonce in CSP header: {csp_header}"
            )

            nonce_value = nonce_match.group(1)

            # Verify the nonce appears exactly once in the header
            # (it should only be in script-src)
            occurrences = csp_header.count(f"nonce-{nonce_value}")
            assert occurrences == 1, (
                f"Nonce appears {occurrences} times in CSP header "
                f"(expected exactly 1). Header: {csp_header}"
            )

            # Verify it's specifically in the script-src directive
            script_src_match = re.search(
                r"script-src\s+([^;]+)", csp_header
            )
            assert script_src_match is not None, (
                f"Could not parse script-src directive from: {csp_header}"
            )
            script_src_value = script_src_match.group(1)
            assert f"'nonce-{nonce_value}'" in script_src_value, (
                f"Nonce not in script-src directive. "
                f"script-src: {script_src_value}"
            )
