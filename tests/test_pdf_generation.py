import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from app import create_app, db
from app.models import User, ThreatModel, Threat
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
    print('✓ User created')

    # Create threat model
    m = ThreatModel(
        name='Test Threat Model',
        description='This is a test model for PDF generation',
        methodology='STRIDE',
        user_id=u.id
    )
    db.session.add(m)
    db.session.commit()
    print('✓ Threat model created')

    # Add threats to the model
    threats_data = [
        {
            'title': 'SQL Injection Attack',
            'description': 'Attacker could inject malicious SQL code',
            'stride_category': 'Tampering',
            'damage': 5,
            'reproducibility': 4,
            'exploitability': 5,
            'affected_users': 5,
            'discoverability': 4,
            'countermeasure': 'Use parameterized queries',
            'status': 'Open'
        },
        {
            'title': 'Authentication Bypass',
            'description': 'Weak authentication mechanism',
            'stride_category': 'Spoofing',
            'damage': 5,
            'reproducibility': 3,
            'exploitability': 4,
            'affected_users': 5,
            'discoverability': 3,
            'countermeasure': 'Implement multi-factor authentication',
            'status': 'In Progress'
        },
        {
            'title': 'Information Disclosure',
            'description': 'Sensitive data could be exposed',
            'stride_category': 'Information Disclosure',
            'damage': 3,
            'reproducibility': 2,
            'exploitability': 3,
            'affected_users': 4,
            'discoverability': 2,
            'countermeasure': 'Encrypt sensitive data',
            'status': 'Resolved'
        }
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
    print(f'✓ Created {len(threats_data)} threats')

    # Verify threats were saved
    saved_threats = Threat.query.filter_by(model_id=m.id).all()
    print(f'\n--- Threat Verification ---')
    for idx, t in enumerate(saved_threats, 1):
        print(f'{idx}. {t.title}')
        print(f'   - STRIDE: {t.stride_category}')
        print(f'   - DREAD Score: {t.dread_score}')
        print(f'   - Risk Level: {t.risk_level}')
        print(f'   - Status: {t.status}')

    # Test PDF generation
    print(f'\n--- PDF Generation Test ---')
    client = app.test_client()
    
    # Log in
    resp_login = client.post('/auth/login', data={'username': 'testuser', 'password': 'Testpass1'}, follow_redirects=True)
    print(f'✓ Login status: {resp_login.status_code}')
    
    # Generate PDF
    resp_pdf = client.get(f'/reports/{m.id}/pdf')
    print(f'✓ PDF request status: {resp_pdf.status_code}')
    
    if resp_pdf.status_code == 200:
        pdf_data = resp_pdf.get_data()
        print(f'✓ PDF size: {len(pdf_data)} bytes')
        
        if len(pdf_data) > 0:
            # Check for PDF header
            if pdf_data.startswith(b'%PDF'):
                print('✓ PDF header is valid')
            else:
                print('✗ PDF header missing or invalid')
                print(f'  First bytes: {pdf_data[:20]}')
            
            # Try to extract text from PDF
            try:
                import pprint
                # Look for text content in PDF stream
                pdf_str = pdf_data.decode('latin-1', errors='ignore')
                
                if 'Threat Analysis Report' in pdf_str:
                    print('✓ Report title found in PDF')
                else:
                    print('✗ Report title NOT found')
                
                if m.name in pdf_str:
                    print(f'✓ Model name "{m.name}" found in PDF')
                else:
                    print(f'✗ Model name NOT found')
                
                if 'STRIDE' in pdf_str or 'Methodology' in pdf_str:
                    print('✓ Methodology information found in PDF')
                else:
                    print('✗ Methodology NOT found')
                
                # Check for threat data
                threat_found = False
                for threat in saved_threats:
                    if threat.title in pdf_str:
                        print(f'✓ Threat "{threat.title}" found in PDF')
                        threat_found = True
                        break
                
                if not threat_found:
                    print('✗ No threat titles found in PDF')
                    print('  Searching for threat data...')
                    if 'SQL' in pdf_str or 'Injection' in pdf_str:
                        print('  ✓ Found SQL/Injection references')
                    if 'Authentication' in pdf_str:
                        print('  ✓ Found Authentication reference')
                    if 'Information' in pdf_str:
                        print('  ✓ Found Information reference')
                
                if 'Critical' in pdf_str or 'Medium' in pdf_str or 'High' in pdf_str or 'Low' in pdf_str:
                    print('✓ Risk level data found in PDF')
                else:
                    print('✗ Risk level data NOT found')
                    
            except Exception as e:
                print(f'Error analyzing PDF content: {e}')
            
            # Save PDF to file for manual inspection
            import tempfile
            temp_dir = tempfile.gettempdir()
            pdf_path = os.path.join(temp_dir, 'test_report.pdf')
            with open(pdf_path, 'wb') as f:
                f.write(pdf_data)
            print(f'✓ PDF saved to {pdf_path} for inspection')
        else:
            print('✗ PDF is empty!')
    else:
        print(f'✗ PDF generation failed: {resp_pdf.status_code}')
        print(f'Response: {resp_pdf.get_data(as_text=True)[:200]}')

print('\n✅ PDF generation test completed!')
