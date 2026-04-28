import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, ThreatModel, Threat
from datetime import datetime
import tempfile
from PyPDF2 import PdfReader

print('=' * 70)
print('COMPREHENSIVE PDF REPORT TESTING')
print('=' * 70)

app = create_app()
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

with app.app_context():
    # Setup
    db.drop_all()
    db.create_all()
    
    print('\n1. USER SETUP')
    print('-' * 70)
    u = User(username='testuser', email='test@example.com', role='user')
    u.set_password('Testpass1')
    db.session.add(u)
    db.session.commit()
    print('✓ User created (ID: {}, Role: {})'.format(u.id, u.role))
    
    print('\n2. THREAT MODEL CREATION')
    print('-' * 70)
    m = ThreatModel(
        name='E-Commerce Platform Security Assessment',
        description='Comprehensive threat assessment for the e-commerce application',
        methodology='STRIDE',
        status='Active',
        user_id=u.id
    )
    db.session.add(m)
    db.session.commit()
    print('✓ Threat model created')
    print('  - Name: {}'.format(m.name))
    print('  - Methodology: {}'.format(m.methodology))
    print('  - Status: {}'.format(m.status))
    
    print('\n3. THREAT POPULATION')
    print('-' * 70)
    
    threats_data = [
        {
            'title': 'SQL Injection in Product Search',
            'description': 'Attacker could inject SQL code through product search parameters to access/modify database',
            'stride_category': 'Tampering',
            'damage': 5, 'reproducibility': 4, 'exploitability': 5, 'affected_users': 5, 'discoverability': 4,
            'countermeasure': 'Implement parameterized queries and input validation',
            'status': 'Open'
        },
        {
            'title': 'Authentication Bypass via Cookie Manipulation',
            'description': 'Session cookies are not properly validated, allowing attackers to forge sessions',
            'stride_category': 'Spoofing',
            'damage': 5, 'reproducibility': 3, 'exploitability': 4, 'affected_users': 5, 'discoverability': 3,
            'countermeasure': 'Implement secure session management with CSRF tokens',
            'status': 'In Progress'
        },
        {
            'title': 'Insufficient Encryption of Payment Data',
            'description': 'Payment information stored without proper encryption',
            'stride_category': 'Information Disclosure',
            'damage': 5, 'reproducibility': 1, 'exploitability': 3, 'affected_users': 5, 'discoverability': 2,
            'countermeasure': 'Use AES-256 encryption for sensitive payment data',
            'status': 'Resolved'
        },
        {
            'title': 'Cross-Site Scripting (XSS) in Comments',
            'description': 'User comments are not sanitized, allowing XSS attacks',
            'stride_category': 'Tampering',
            'damage': 3, 'reproducibility': 5, 'exploitability': 5, 'affected_users': 4, 'discoverability': 5,
            'countermeasure': 'Implement output encoding and CSP headers',
            'status': 'Open'
        },
        {
            'title': 'Privilege Escalation via Direct Object Reference',
            'description': 'Users can modify URLs to access other users orders',
            'stride_category': 'Elevation of Privilege',
            'damage': 4, 'reproducibility': 4, 'exploitability': 4, 'affected_users': 3, 'discoverability': 3,
            'countermeasure': 'Implement proper authorization checks',
            'status': 'In Progress'
        },
    ]

    for threat_data in threats_data:
        threat = Threat(
            title=threat_data['title'],
            description=threat_data['description'],
            stride_category=threat_data['stride_category'],
            damage=threat_data['damage'],
            reproducibility=threat_data['reproducibility'],
            exploitability=threat_data['exploitability'],
            affected_users=threat_data['affected_users'],
            discoverability=threat_data['discoverability'],
            countermeasure=threat_data['countermeasure'],
            status=threat_data['status'],
            model_id=m.id
        )
        threat.calculate_dread()
        db.session.add(threat)
    
    db.session.commit()
    print('✓ Added {} threats'.format(len(threats_data)))
    
    saved_threats = Threat.query.filter_by(model_id=m.id).all()
    for idx, t in enumerate(saved_threats, 1):
        print('  {}. {} [{}] - DREAD: {} - Risk: {}'.format(
            idx, t.title, t.stride_category, t.dread_score, t.risk_level))
    
    print('\n4. PDF GENERATION TEST')
    print('-' * 70)
    
    client = app.test_client()
    
    # Authentication
    resp_login = client.post('/auth/login', data={'username': 'testuser', 'password': 'Testpass1'}, follow_redirects=True)
    assert resp_login.status_code == 200, 'Login failed'
    print('✓ User authenticated')
    
    # Generate PDF
    resp_pdf = client.get(f'/reports/{m.id}/pdf')
    assert resp_pdf.status_code == 200, f'PDF generation failed with status {resp_pdf.status_code}'
    print('✓ PDF generated successfully')
    
    pdf_data = resp_pdf.get_data()
    assert len(pdf_data) > 0, 'PDF is empty'
    print('✓ PDF size: {} bytes'.format(len(pdf_data)))
    
    assert pdf_data.startswith(b'%PDF'), 'Invalid PDF header'
    print('✓ PDF header valid')
    
    print('\n5. PDF CONTENT VERIFICATION')
    print('-' * 70)
    
    # Extract and verify content
    temp_dir = tempfile.gettempdir()
    pdf_path = os.path.join(temp_dir, 'comprehensive_report.pdf')
    with open(pdf_path, 'wb') as f:
        f.write(pdf_data)
    
    pdf_reader = PdfReader(pdf_path)
    assert len(pdf_reader.pages) > 0, 'PDF has no pages'
    print('✓ PDF has {} pages'.format(len(pdf_reader.pages)))
    
    all_text = ""
    for page in pdf_reader.pages:
        all_text += page.extract_text()
    
    # Verification checks
    checks = [
        ('Report Title', 'Threat Analysis Report'),
        ('Model Name', m.name),
        ('Methodology', 'STRIDE'),
        ('Model Status', 'Active'),
        ('Threat Count', '5'),
        ('First Threat', threats_data[0]['title']),
        ('Critical Risk', 'Critical'),
        ('High Risk', 'High'),
        ('SQL Injection', 'SQL Injection'),
        ('XSS Prevention', 'XSS'),
        ('Encryption Countermeasure', 'AES'),
        ('DREAD Score', '4.6'),
    ]
    
    all_pass = True
    for check_name, search_term in checks:
        if search_term in all_text:
            print('✓ {}: "{}"'.format(check_name, search_term))
        else:
            print('✗ {} NOT FOUND: "{}"'.format(check_name, search_term))
            all_pass = False
    
    print('\n6. AUTHORIZATION TESTS')
    print('-' * 70)
    
    # Create another user
    u2 = User(username='otheruser', email='other@example.com', role='user')
    u2.set_password('Testpass1')
    db.session.add(u2)
    db.session.commit()
    print('✓ Second user created')
    
    # Create a model for user 2
    m2 = ThreatModel(name='User 2 Model', description='Model by user 2', methodology='STRIDE', user_id=u2.id)
    db.session.add(m2)
    db.session.commit()
    
    # Login as second user
    client.get('/auth/logout')
    resp_login2 = client.post('/auth/login', data={'username': 'otheruser', 'password': 'Testpass1'}, follow_redirects=True)
    assert resp_login2.status_code == 200, 'Second user login failed'
    print('✓ Second user authenticated')
    
    # Try to access first user's report
    resp_forbidden = client.get(f'/reports/{m.id}/pdf')
    assert resp_forbidden.status_code == 403, f'Authorization check failed - got {resp_forbidden.status_code}'
    print('✓ Authorization check PASSED - access denied to other user')
    
    print('\n' + '=' * 70)
    if all_pass:
        print('✅ ALL TESTS PASSED! PDF REPORT GENERATION WORKING CORRECTLY')
    else:
        print('⚠️ SOME CHECKS FAILED - Review PDF content')
    print('=' * 70)

print('\nTest completed successfully!')
