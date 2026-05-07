"""Property-based tests for SMTP configuration validation.

Tests verify that validate_smtp_config() produces correct log messages
when SMTP environment variables are partially configured or when
SMTP_PORT contains a non-numeric value.

Validates: Requirements 5.1, 5.3
"""

import logging
import os
from unittest.mock import patch

import pytest
from flask import Flask
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from app.auth.routes import validate_smtp_config


# The three main SMTP variables that validate_smtp_config checks
SMTP_MAIN_VARS = ['SMTP_SERVER', 'SENDER_EMAIL', 'SENDER_PASSWORD']

# Strategy for generating non-empty subset selections (which vars are present)
# We use sets of indices into SMTP_MAIN_VARS to pick which are present
present_vars_strategy = st.frozensets(
    st.sampled_from(SMTP_MAIN_VARS),
    min_size=1,
    max_size=2,
)

# Strategy for generating non-empty values for "present" SMTP vars
smtp_value_strategy = st.text(
    alphabet=st.characters(whitelist_categories=('L', 'N', 'P'), whitelist_characters='.-_@'),
    min_size=1,
    max_size=100,
).filter(lambda s: s.strip() != '')

# Strategy for generating non-numeric SMTP_PORT values
# Must be strings that cannot be parsed as int
# Exclude null characters since they can't be set as env vars on Windows
non_numeric_port_strategy = st.text(
    alphabet=st.characters(blacklist_characters='\x00'),
    min_size=1,
    max_size=50,
).filter(lambda s: s.strip() != '' and not _is_int(s.strip()))


def _is_int(s):
    """Check if a string can be parsed as an integer."""
    try:
        int(s)
        return True
    except (ValueError, TypeError):
        return False


def _create_minimal_app():
    """Create a minimal Flask app for testing."""
    app = Flask(__name__)
    app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-secret-key',
    })
    return app


class _RecordCapture(logging.Handler):
    """Simple log handler that captures log records."""

    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


class TestPartialSMTPConfigWarning:
    """Property 5: Partial SMTP config warning identifies missing variables.

    For any non-empty subset of SMTP variables (SMTP_SERVER, SENDER_EMAIL,
    SENDER_PASSWORD) that are present while the remaining are absent, calling
    validate_smtp_config() SHALL produce a WARNING log that lists exactly the
    names of the absent variables.

    **Validates: Requirements 5.1**
    """

    @settings(max_examples=100)
    @given(
        present_vars=present_vars_strategy,
        values=st.lists(smtp_value_strategy, min_size=3, max_size=3),
    )
    def test_partial_smtp_config_warns_with_missing_var_names(self, present_vars, values):
        """For any non-empty proper subset of SMTP vars that are present,
        the WARNING log SHALL list exactly the absent variable names."""
        # present_vars is a frozenset with 1 or 2 of the 3 SMTP vars
        # This guarantees at least 1 var is missing (since max_size=2)
        absent_vars = set(SMTP_MAIN_VARS) - set(present_vars)
        assert len(absent_vars) >= 1, "Test logic error: need at least one absent var"

        # Build environment: present vars get non-empty values, absent vars get empty
        env_overrides = {}
        value_iter = iter(values)
        for var in SMTP_MAIN_VARS:
            if var in present_vars:
                env_overrides[var] = next(value_iter)
            else:
                env_overrides[var] = ''
                # consume the value anyway to keep iteration consistent
                next(value_iter)

        # Set a valid SMTP_PORT so it doesn't interfere
        env_overrides['SMTP_PORT'] = '587'

        app = _create_minimal_app()
        capture = _RecordCapture()
        capture.setLevel(logging.DEBUG)
        app.logger.addHandler(capture)
        app.logger.setLevel(logging.DEBUG)

        try:
            with patch.dict(os.environ, env_overrides, clear=False):
                validate_smtp_config(app)
        finally:
            app.logger.removeHandler(capture)

        # Filter for WARNING level records
        warning_records = [r for r in capture.records if r.levelno == logging.WARNING]

        assert len(warning_records) >= 1, (
            f"Expected at least one WARNING log when vars {absent_vars} are missing. "
            f"Got records: {[(r.levelno, r.getMessage()) for r in capture.records]}"
        )

        # Check that the warning message contains each absent variable name
        warning_messages = ' '.join(r.getMessage() for r in warning_records)
        for var_name in absent_vars:
            assert var_name in warning_messages, (
                f"Missing variable name '{var_name}' not found in WARNING log: "
                f"{warning_messages}"
            )


class TestNonNumericSMTPPortError:
    """Property 6: Non-numeric SMTP_PORT triggers error log.

    For any string value of SMTP_PORT that cannot be parsed as an integer,
    calling validate_smtp_config() SHALL produce an ERROR log containing
    that invalid value.

    **Validates: Requirements 5.3**
    """

    @settings(max_examples=100)
    @given(
        invalid_port=non_numeric_port_strategy,
    )
    def test_non_numeric_smtp_port_triggers_error_with_value(self, invalid_port):
        """For any non-numeric SMTP_PORT string, the ERROR log SHALL contain
        that invalid value."""
        # We need at least one SMTP var present so the function doesn't
        # short-circuit at the "all absent" INFO branch before checking port.
        # Set all three present so we reach the port validation logic.
        env_overrides = {
            'SMTP_SERVER': 'smtp.example.com',
            'SENDER_EMAIL': 'test@example.com',
            'SENDER_PASSWORD': 'password123',
            'SMTP_PORT': invalid_port,
        }

        app = _create_minimal_app()
        capture = _RecordCapture()
        capture.setLevel(logging.DEBUG)
        app.logger.addHandler(capture)
        app.logger.setLevel(logging.DEBUG)

        try:
            with patch.dict(os.environ, env_overrides, clear=False):
                validate_smtp_config(app)
        finally:
            app.logger.removeHandler(capture)

        # Filter for ERROR level records
        error_records = [r for r in capture.records if r.levelno == logging.ERROR]

        assert len(error_records) >= 1, (
            f"Expected at least one ERROR log for non-numeric SMTP_PORT '{invalid_port}'. "
            f"Got records: {[(r.levelno, r.getMessage()) for r in capture.records]}"
        )

        # The error message must contain the invalid port value
        error_messages = ' '.join(r.getMessage() for r in error_records)
        # Use the stripped version since validate_smtp_config strips the value
        stripped_port = invalid_port.strip()
        assert stripped_port in error_messages, (
            f"Invalid port value '{stripped_port}' not found in ERROR log: "
            f"{error_messages}"
        )
