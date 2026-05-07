"""Unit tests for DFD Editor toolbar event dispatch.

Validates Requirement 3.4: When a toolbar button is clicked, the DFD_Editor
SHALL invoke the corresponding editor function via data-action attributes
and event delegation.

These tests use the Flask test client to render the DFD editor page and
verify the HTML output contains the correct data-action attributes and
no inline onclick handlers.
"""

import re
import pytest
from app import create_app
from app.models import db, User, ThreatModel


@pytest.fixture
def app():
    """Create a Flask application configured for testing."""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'SERVER_NAME': 'localhost',
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a Flask test client."""
    return app.test_client()


@pytest.fixture
def authenticated_user(app, client):
    """Create a test user and log them in, returning the user and a threat model."""
    with app.app_context():
        user = User(username='testuser', email='test@example.com')
        user.set_password('TestPass123!')
        db.session.add(user)
        db.session.commit()

        user_id = user.id

        model = ThreatModel(
            name='Test Model',
            description='A test threat model',
            user_id=user_id,
        )
        db.session.add(model)
        db.session.commit()

        model_id = model.id

    # Log in the user
    client.post('/auth/login', data={
        'username': 'testuser',
        'password': 'TestPass123!',
    }, follow_redirects=True)

    return {'user_id': user_id, 'model_id': model_id}


@pytest.fixture
def editor_html(client, authenticated_user):
    """Fetch the DFD editor page HTML for the test threat model."""
    model_id = authenticated_user['model_id']
    response = client.get(f'/dfd/{model_id}/edit')
    assert response.status_code == 200, (
        f"Expected 200 but got {response.status_code} for DFD editor page"
    )
    return response.data.decode('utf-8')


class TestDFDToolbarNoInlineHandlers:
    """Regression tests: DFD editor template must not use inline onclick attributes."""

    def test_no_onclick_attributes_in_toolbar(self, editor_html):
        """The DFD editor toolbar buttons must not have onclick attributes.

        Validates: Requirements 3.1
        Inline onclick handlers are blocked by CSP. All event handling
        must use addEventListener via data-action attributes.
        """
        # Find the toolbar section
        toolbar_match = re.search(
            r'<div[^>]*class="[^"]*dfd-toolbar[^"]*"[^>]*>(.*?)</div>',
            editor_html,
            re.DOTALL,
        )
        assert toolbar_match is not None, "Could not find .dfd-toolbar in editor HTML"
        toolbar_html = toolbar_match.group(1)

        # Verify no onclick attributes exist in toolbar buttons
        onclick_matches = re.findall(r'onclick\s*=', toolbar_html, re.IGNORECASE)
        assert len(onclick_matches) == 0, (
            f"Found {len(onclick_matches)} onclick attribute(s) in toolbar. "
            "All event handling should use data-action attributes instead."
        )

    def test_no_onclick_on_any_button_in_page(self, editor_html):
        """No button element in the entire page should have an onclick attribute.

        Validates: Requirements 3.1
        """
        # Find all button elements with onclick
        buttons_with_onclick = re.findall(
            r'<button[^>]*onclick\s*=[^>]*>',
            editor_html,
            re.IGNORECASE,
        )
        assert len(buttons_with_onclick) == 0, (
            f"Found {len(buttons_with_onclick)} button(s) with onclick attributes: "
            f"{buttons_with_onclick}"
        )


class TestDFDToolbarDataActions:
    """Tests that all required data-action attributes are present in the template."""

    # Expected data-action values that must be present in the toolbar
    EXPECTED_ACTIONS = [
        'add-element',
        'start-connection',
        'delete-selected',
        'undo',
        'redo',
        'clear-all',
        'save-canvas',
    ]

    # Expected element types for add-element buttons
    EXPECTED_ELEMENT_TYPES = [
        'process',
        'datastore',
        'external',
        'trustBoundary',
    ]

    def test_all_data_action_values_present(self, editor_html):
        """Each expected data-action value must appear in the toolbar.

        Validates: Requirements 3.2, 3.4
        """
        for action in self.EXPECTED_ACTIONS:
            pattern = rf'data-action\s*=\s*["\']{ re.escape(action) }["\']'
            assert re.search(pattern, editor_html), (
                f"Missing data-action=\"{action}\" in DFD editor template"
            )

    def test_add_element_buttons_have_element_type(self, editor_html):
        """Each add-element button must have a data-element-type attribute.

        Validates: Requirements 3.2, 3.4
        """
        for element_type in self.EXPECTED_ELEMENT_TYPES:
            pattern = (
                rf'data-action\s*=\s*["\']add-element["\']'
                rf'[^>]*data-element-type\s*=\s*["\']{ re.escape(element_type) }["\']'
            )
            assert re.search(pattern, editor_html), (
                f"Missing button with data-action=\"add-element\" "
                f"data-element-type=\"{element_type}\" in DFD editor template"
            )

    def test_each_action_has_at_least_one_button(self, editor_html):
        """Each data-action value should correspond to exactly one button (no duplicates).

        Validates: Requirements 3.2
        """
        for action in self.EXPECTED_ACTIONS:
            if action == 'add-element':
                # add-element has multiple buttons (one per element type)
                continue
            pattern = rf'data-action\s*=\s*["\']{ re.escape(action) }["\']'
            matches = re.findall(pattern, editor_html)
            assert len(matches) == 1, (
                f"Expected exactly 1 button with data-action=\"{action}\", "
                f"found {len(matches)}"
            )

    def test_add_element_has_four_buttons(self, editor_html):
        """There should be exactly 4 add-element buttons (one per DFD element type).

        Validates: Requirements 3.2
        """
        pattern = r'data-action\s*=\s*["\']add-element["\']'
        matches = re.findall(pattern, editor_html)
        assert len(matches) == 4, (
            f"Expected 4 add-element buttons, found {len(matches)}"
        )


class TestDFDToolbarEventDelegation:
    """Tests that the JS event delegation handles known actions and ignores unknown ones."""

    def test_toolbar_has_dfd_toolbar_class(self, editor_html):
        """The toolbar container must have the .dfd-toolbar class for event delegation.

        Validates: Requirements 3.3
        The JS bindToolbarEvents() queries '.dfd-toolbar' to attach the
        delegated click listener.
        """
        assert 'class="dfd-toolbar"' in editor_html or "dfd-toolbar" in editor_html, (
            "Could not find element with class 'dfd-toolbar' in editor HTML"
        )

    def test_dfd_editor_js_included(self, editor_html):
        """The dfd_editor.js script must be included in the page.

        Validates: Requirements 3.3
        """
        assert 'dfd_editor.js' in editor_html, (
            "dfd_editor.js is not included in the DFD editor page"
        )

    def test_inline_script_has_nonce(self, editor_html):
        """The inline script block must have a nonce attribute for CSP compliance.

        Validates: Requirements 4.3
        """
        # Check that the inline script has a nonce attribute
        pattern = r'<script\s+nonce\s*=\s*"[^"]+"\s*>'
        assert re.search(pattern, editor_html), (
            "Inline script block is missing nonce attribute"
        )

    def test_unknown_data_action_silently_ignored(self):
        """Unknown data-action values should be silently ignored by the switch statement.

        Validates: Requirements 3.4
        This is verified by reading the JS source and confirming the switch
        statement has no default case that throws or alerts.
        """
        # Read the JS file to verify the switch has no error-throwing default
        import os
        js_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'app', 'static', 'js', 'dfd_editor.js'
        )
        with open(js_path, 'r') as f:
            js_content = f.read()

        # Verify the switch statement exists for data-action dispatch
        assert "switch (action)" in js_content or "switch(action)" in js_content, (
            "Expected switch statement on action variable in dfd_editor.js"
        )

        # Verify there's no default case that throws an error or shows an alert
        # The switch should simply fall through for unknown actions
        switch_match = re.search(
            r'switch\s*\(action\)\s*\{(.*?)\n\s*\}',
            js_content,
            re.DOTALL,
        )
        assert switch_match is not None, (
            "Could not find switch(action) block in dfd_editor.js"
        )
        switch_body = switch_match.group(1)

        # Verify no default case that throws or alerts
        assert 'default:' not in switch_body or (
            'throw' not in switch_body and 'alert' not in switch_body
        ), (
            "The switch statement should silently ignore unknown data-action values "
            "(no throw or alert in default case)"
        )
