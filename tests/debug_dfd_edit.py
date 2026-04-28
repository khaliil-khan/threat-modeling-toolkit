import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, ThreatModel, DFDData
from datetime import datetime

app = create_app()
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

with app.app_context():
    # Recreate database
    db.drop_all()
    db.create_all()

    # Create user
    u = User(username='testuser', email='test@example.com', role='user')
    u.set_password('Testpass1')
    db.session.add(u)
    db.session.commit()

    # Create threat model
    m = ThreatModel(name='Test Model', description='For DFD verification', methodology='STRIDE', user_id=u.id)
    db.session.add(m)
    db.session.commit()

    # Create DFDData
    dfd = DFDData(model_id=m.id, canvas_json='{}', updated_at=datetime.utcnow())
    db.session.add(dfd)
    db.session.commit()

    # Use test client to GET the edit DFD page (requires login)
    client = app.test_client()
    
    # Log in
    resp_login = client.post('/auth/login', data={'username': 'testuser', 'password': 'Testpass1'}, follow_redirects=True)
    print('Login POST status:', resp_login.status_code)
    
    # Try to access edit_dfd
    resp_edit = client.get(f'/dfd/{m.id}/edit')
    print('GET /dfd/{id}/edit status:', resp_edit.status_code)
    
    if resp_edit.status_code == 200:
        print('✓ Edit page loaded successfully')
        # Check if the page contains the expected elements
        content = resp_edit.get_data(as_text=True)
        if 'dfdCanvas' in content:
            print('✓ Canvas element found')
        else:
            print('✗ Canvas element NOT found')
        if 'dfd_editor.js' in content:
            print('✓ DFD editor script found')
        else:
            print('✗ DFD editor script NOT found')
    else:
        print('✗ Edit page failed to load')
        print('Response content (first 500 chars):')
        print(resp_edit.get_data(as_text=True)[:500])

print('Debug script completed')
