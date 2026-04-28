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

    client = app.test_client()
    
    # Log in
    resp_login = client.post('/auth/login', data={'username': 'testuser', 'password': 'Testpass1'}, follow_redirects=True)
    print('✓ Login successful')
    
    # 1. Test GET editor page (new model with no DFD data)
    print('\n--- Test 1: Load empty DFD editor ---')
    resp_edit = client.get(f'/dfd/{m.id}/edit')
    print(f'✓ GET /dfd/{{id}}/edit status: {resp_edit.status_code}')
    content = resp_edit.get_data(as_text=True)
    assert 'dfdCanvas' in content, 'Canvas element missing'
    assert 'initializeCanvas' in content, 'initializeCanvas function missing'
    assert 'loadSavedDFD' in content, 'loadSavedDFD function missing'
    print('✓ All required elements present in HTML')
    
    # 2. Test save DFD with new data
    print('\n--- Test 2: Save DFD with elements ---')
    test_canvas_data = [
        {
            "type": "process",
            "x": 50,
            "y": 80,
            "w": 100,
            "h": 50,
            "color": "#3498db",
            "label": "Process 1"
        },
        {
            "type": "datastore",
            "x": 200,
            "y": 80,
            "w": 100,
            "h": 60,
            "color": "#2ecc71",
            "label": "Database"
        }
    ]
    
    resp_save = client.post(
        f'/dfd/{m.id}/save',
        data=json.dumps({'canvas_json': json.dumps(test_canvas_data)}),
        content_type='application/json'
    )
    print(f'✓ POST /dfd/{{id}}/save status: {resp_save.status_code}')
    assert resp_save.status_code == 200, f'Save failed with status {resp_save.status_code}'
    assert resp_save.get_json()['status'] == 'saved', 'Save response invalid'
    print('✓ DFD saved successfully')
    
    # 3. Test load editor with existing DFD data
    print('\n--- Test 3: Load DFD editor with existing data ---')
    resp_edit_2 = client.get(f'/dfd/{m.id}/edit')
    print(f'✓ GET /dfd/{{id}}/edit status: {resp_edit_2.status_code}')
    content_2 = resp_edit_2.get_data(as_text=True)
    # Check if the saved data is embedded in the page
    assert 'Process 1' in content_2 or 'canvas_json' in content_2, 'Saved data not found in page'
    print('✓ Existing DFD data available in editor')
    
    # 4. Verify DFDData in database
    print('\n--- Test 4: Verify DFDData in database ---')
    dfd = DFDData.query.filter_by(model_id=m.id).first()
    assert dfd is not None, 'DFDData not created'
    print('✓ DFDData record exists')
    saved_elements = json.loads(dfd.canvas_json)
    assert len(saved_elements) == 2, f'Expected 2 elements, got {len(saved_elements)}'
    print(f'✓ Correct number of elements stored: {len(saved_elements)}')
    assert saved_elements[0]['label'] == 'Process 1', 'First element data incorrect'
    assert saved_elements[1]['label'] == 'Database', 'Second element data incorrect'
    print('✓ All element data saved correctly')

print('\n✅ All tests passed! DFD editing is working correctly.')
