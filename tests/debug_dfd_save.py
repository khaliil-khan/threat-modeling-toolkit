import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
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

    # Use test client to login and test save
    client = app.test_client()
    
    # Log in
    resp_login = client.post('/auth/login', data={'username': 'testuser', 'password': 'Testpass1'}, follow_redirects=True)
    print('Login POST status:', resp_login.status_code)
    
    # Test save DFD with some canvas data
    test_canvas_data = [
        {
            "type": "process",
            "x": 50,
            "y": 80,
            "w": 100,
            "h": 50,
            "color": "#3498db",
            "label": "Process"
        }
    ]
    
    resp_save = client.post(
        f'/dfd/{m.id}/save',
        data=json.dumps({'canvas_json': json.dumps(test_canvas_data)}),
        content_type='application/json'
    )
    
    print('POST /dfd/{id}/save status:', resp_save.status_code)
    print('Save response:', resp_save.get_json())
    
    # Check if DFDData was created
    dfd = DFDData.query.filter_by(model_id=m.id).first()
    if dfd:
        print('✓ DFDData created')
        print('Canvas JSON:', dfd.canvas_json[:100], '...' if len(dfd.canvas_json) > 100 else '')
    else:
        print('✗ DFDData NOT created')

print('Save test completed')
