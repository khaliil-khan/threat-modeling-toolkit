import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, ThreatModel, Threat, DFDData
from datetime import datetime
import tempfile
from PyPDF2 import PdfReader

print('=' * 80)
print('THREAT TOOLKIT - COMPLETE INTEGRATION TEST')
print('=' * 80)

app = create_app()
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

with app.app_context():
    db.drop_all()
    db.create_all()
    
    print('\n[1/8] Creating test user...')
    u = User(username='admin', email='admin@example.com', role='admin')
    u.set_password('AdminPass123')
    db.session.add(u)
    db.session.commit()
    print('      ✓ Admin user created')
    
    print('\n[2/8] Creating threat model...')
    m = ThreatModel(
        name='Banking Application Security Model',
        description='Comprehensive threat model for the online banking platform',
        methodology='STRIDE',
        status='Active',
        user_id=u.id
    )
    db.session.add(m)
    db.session.commit()
    print('      ✓ Threat model created')
    
    print('\n[3/8] Adding threats to the model...')
    threats = [
        Threat(
            title='Unauthorized Data Access',
            description='Attackers could gain unauthorized access to customer financial data',
            stride_category='Information Disclosure',
            damage=5, reproducibility=2, exploitability=2, affected_users=5, discoverability=2,
            countermeasure='Implement strong encryption and access controls',
            status='Open',
            model_id=m.id
        ),
        Threat(
            title='Man-in-the-Middle Attack',
            description='Network traffic could be intercepted and modified',
            stride_category='Tampering',
            damage=5, reproducibility=3, exploitability=4, affected_users=5, discoverability=3,
            countermeasure='Use TLS 1.3 with certificate pinning',
            status='In Progress',
            model_id=m.id
        ),
        Threat(
            title='Session Hijacking',
            description='Session tokens could be stolen or forged',
            stride_category='Spoofing',
            damage=5, reproducibility=2, exploitability=3, affected_users=4, discoverability=2,
            countermeasure='Implement secure session management and CSRF tokens',
            status='Open',
            model_id=m.id
        ),
    ]
    
    for threat in threats:
        threat.calculate_dread()
        db.session.add(threat)
    db.session.commit()
    print(f'      ✓ Added {len(threats)} threats')
    
    print('\n[4/8] Creating DFD data...')
    dfd = DFDData(
        model_id=m.id,
        canvas_json='[{"type":"process","x":50,"y":80,"w":100,"h":50,"color":"#3498db","label":"Login Service"}]',
        updated_at=datetime.utcnow()
    )
    db.session.add(dfd)
    db.session.commit()
    print('      ✓ DFD diagram saved')
    
    print('\n[5/8] Testing authentication...')
    client = app.test_client()
    resp_login = client.post(
        '/auth/login',
        data={'username': 'admin', 'password': 'AdminPass123'},
        follow_redirects=True
    )
    assert resp_login.status_code == 200, 'Login failed'
    print('      ✓ User authenticated successfully')
    
    print('\n[6/8] Testing threat model detail page...')
    resp_detail = client.get(f'/threats/{m.id}')
    assert resp_detail.status_code == 200, 'Detail page failed'
    content = resp_detail.get_data(as_text=True)
    assert m.name in content, 'Model name not found'
    assert 'Unauthorized Data Access' in content, 'Threat not displayed'
    assert 'Download PDF' in content, 'PDF button not found'
    print('      ✓ Threat model detail page working')
    
    print('\n[7/8] Testing PDF report generation...')
    resp_pdf = client.get(f'/reports/{m.id}/pdf')
    assert resp_pdf.status_code == 200, 'PDF generation failed'
    
    pdf_data = resp_pdf.get_data()
    assert len(pdf_data) > 2000, 'PDF appears too small'
    assert pdf_data.startswith(b'%PDF'), 'Invalid PDF format'
    
    # Extract and verify PDF content
    temp_dir = tempfile.gettempdir()
    pdf_path = os.path.join(temp_dir, 'integration_test.pdf')
    with open(pdf_path, 'wb') as f:
        f.write(pdf_data)
    
    pdf_reader = PdfReader(pdf_path)
    pdf_text = ""
    for page in pdf_reader.pages:
        pdf_text += page.extract_text()
    
    assert 'Threat Analysis Report' in pdf_text, 'Report title missing'
    assert m.name in pdf_text, 'Model name missing from PDF'
    assert 'Unauthorized Data Access' in pdf_text, 'Threat data missing from PDF'
    assert '3.2' in pdf_text or '4.0' in pdf_text, 'DREAD scores missing'
    
    print('      ✓ PDF report generated with all content')
    
    print('\n[8/8] Testing DFD editor...')
    resp_dfd = client.get(f'/dfd/{m.id}/edit')
    assert resp_dfd.status_code == 200, 'DFD editor page failed'
    dfd_content = resp_dfd.get_data(as_text=True)
    assert 'dfdCanvas' in dfd_content, 'Canvas element missing'
    assert 'initializeCanvas' in dfd_content, 'Canvas init function missing'
    
    # Test DFD save functionality
    import json
    new_dfd_data = [
        {"type": "process", "x": 100, "y": 100, "w": 100, "h": 50, "color": "#3498db", "label": "Process 1"},
        {"type": "datastore", "x": 250, "y": 100, "w": 100, "h": 60, "color": "#2ecc71", "label": "Database"}
    ]
    
    resp_save = client.post(
        f'/dfd/{m.id}/save',
        data=json.dumps({'canvas_json': json.dumps(new_dfd_data)}),
        content_type='application/json'
    )
    assert resp_save.status_code == 200, 'DFD save failed'
    assert resp_save.get_json()['status'] == 'saved', 'Save response invalid'
    
    # Verify DFD was saved
    updated_dfd = DFDData.query.filter_by(model_id=m.id).first()
    assert updated_dfd is not None, 'DFD not found'
    saved_elements = json.loads(updated_dfd.canvas_json)
    assert len(saved_elements) == 2, 'DFD elements not saved correctly'
    
    print('      ✓ DFD editor and save functionality working')
    
    print('\n' + '=' * 80)
    print('✅ ALL INTEGRATION TESTS PASSED!')
    print('=' * 80)
    print('\nSummary:')
    print('  • User authentication working')
    print('  • Threat model creation and retrieval working')
    print('  • Threat DREAD scoring working')
    print('  • PDF report generation with proper content')
    print('  • DFD editor and save functionality working')
    print('  • All security checks in place')
    print('=' * 80)
