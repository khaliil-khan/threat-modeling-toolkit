#!/usr/bin/env python3
"""
Threat Toolkit - PDF Report Generation Validation
This script validates that all PDF report functionality is working correctly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, ThreatModel, Threat
from datetime import datetime
import tempfile
from PyPDF2 import PdfReader

def print_section(title):
    print(f"\n{'─' * 70}")
    print(f"  {title}")
    print(f"{'─' * 70}")

def print_success(msg):
    print(f"  ✓ {msg}")

def print_error(msg):
    print(f"  ✗ {msg}")

def validate_pdf_generation():
    """Complete validation of PDF report generation"""
    
    print("\n" + "═" * 70)
    print("  THREAT TOOLKIT - PDF REPORT VALIDATION")
    print("═" * 70)
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.drop_all()
        db.create_all()
        
        # Setup
        print_section("1. Setting Up Test Data")
        
        user = User(username='validator', email='validator@test.com', role='user')
        user.set_password('ValidPass123')
        db.session.add(user)
        db.session.commit()
        print_success("Test user created")
        
        model = ThreatModel(
            name='Validation Test Model',
            description='Model for PDF report validation',
            methodology='STRIDE',
            status='Active',
            user_id=user.id
        )
        db.session.add(model)
        db.session.commit()
        print_success(f"Threat model created (ID: {model.id})")
        
        # Add test threats
        test_threats = [
            Threat(title='Threat 1', description='First test threat', stride_category='Spoofing',
                   damage=4, reproducibility=3, exploitability=3, affected_users=4, discoverability=2,
                   countermeasure='Fix 1', status='Open', model_id=model.id),
            Threat(title='Threat 2', description='Second test threat', stride_category='Tampering',
                   damage=5, reproducibility=4, exploitability=4, affected_users=5, discoverability=3,
                   countermeasure='Fix 2', status='In Progress', model_id=model.id),
            Threat(title='Threat 3', description='Third test threat', stride_category='Information Disclosure',
                   damage=4, reproducibility=2, exploitability=2, affected_users=3, discoverability=1,
                   countermeasure='Fix 3', status='Resolved', model_id=model.id),
        ]
        
        for threat in test_threats:
            threat.calculate_dread()
            db.session.add(threat)
        db.session.commit()
        print_success(f"Added {len(test_threats)} test threats")
        
        # Test PDF generation
        print_section("2. Generating PDF Report")
        
        client = app.test_client()
        
        # Login
        resp_login = client.post(
            '/auth/login',
            data={'username': 'validator', 'password': 'ValidPass123'},
            follow_redirects=True
        )
        if resp_login.status_code == 200:
            print_success("User authenticated")
        else:
            print_error(f"Authentication failed: {resp_login.status_code}")
            return False
        
        # Generate PDF
        resp_pdf = client.get(f'/reports/{model.id}/pdf')
        if resp_pdf.status_code != 200:
            print_error(f"PDF generation failed: {resp_pdf.status_code}")
            return False
        
        print_success(f"PDF generated (Status: {resp_pdf.status_code})")
        
        pdf_data = resp_pdf.get_data()
        print_success(f"PDF size: {len(pdf_data)} bytes")
        
        # Validate PDF format
        print_section("3. Validating PDF Format")
        
        if not pdf_data.startswith(b'%PDF'):
            print_error("Invalid PDF header")
            return False
        print_success("PDF header valid (%PDF)")
        
        if len(pdf_data) < 2000:
            print_error("PDF appears too small (< 2KB)")
            return False
        print_success(f"PDF size acceptable ({len(pdf_data)} bytes)")
        
        # Extract and verify content
        print_section("4. Extracting & Verifying Content")
        
        temp_dir = tempfile.gettempdir()
        pdf_path = os.path.join(temp_dir, 'validation_report.pdf')
        
        try:
            with open(pdf_path, 'wb') as f:
                f.write(pdf_data)
            
            pdf_reader = PdfReader(pdf_path)
            num_pages = len(pdf_reader.pages)
            
            if num_pages < 2:
                print_error(f"PDF has only {num_pages} page(s), expected 2+")
                return False
            print_success(f"PDF has {num_pages} pages")
            
            # Extract all text
            all_text = ""
            for page in pdf_reader.pages:
                all_text += page.extract_text()
            
            if not all_text:
                print_error("No text could be extracted from PDF")
                return False
            print_success(f"Extracted {len(all_text)} characters from PDF")
            
        except Exception as e:
            print_error(f"Failed to read PDF: {e}")
            return False
        
        # Validate content
        print_section("5. Content Validation")
        
        content_checks = [
            ('Report Title', 'Threat Analysis Report'),
            ('Model Name', model.name),
            ('Methodology', 'STRIDE'),
            ('First Threat', 'Threat 1'),
            ('DREAD Score', '3.2'),
            ('Risk Level', 'Critical'),
            ('Countermeasure', 'Fix'),
        ]
        
        all_checks_passed = True
        for check_name, search_term in content_checks:
            if search_term in all_text:
                print_success(f"{check_name}: Found '{search_term}'")
            else:
                print_error(f"{check_name}: NOT found '{search_term}'")
                all_checks_passed = False
        
        if not all_checks_passed:
            return False
        
        # Test authorization
        print_section("6. Security Validation")
        
        # Create second user
        user2 = User(username='validator2', email='validator2@test.com', role='user')
        user2.set_password('ValidPass456')
        db.session.add(user2)
        db.session.commit()
        print_success("Second user created")
        
        # Login as second user
        client.get('/auth/logout')
        client.post('/auth/login',
                   data={'username': 'validator2', 'password': 'ValidPass456'},
                   follow_redirects=True)
        
        # Try to access first user's report
        resp_forbidden = client.get(f'/reports/{model.id}/pdf')
        if resp_forbidden.status_code == 403:
            print_success("Authorization enforced (403 Forbidden)")
        else:
            print_error(f"Authorization NOT enforced (got {resp_forbidden.status_code})")
            return False
        
        print_section("VALIDATION RESULTS")
        print("\n  ✅ ALL CHECKS PASSED!")
        print("\n  Summary:")
        print(f"    • PDF Generation: Working ✓")
        print(f"    • PDF Format: Valid ✓")
        print(f"    • Content Extraction: Successful ✓")
        print(f"    • Content Verification: Complete ✓")
        print(f"    • Authorization: Enforced ✓")
        print("\n" + "═" * 70 + "\n")
        
        return True

if __name__ == '__main__':
    try:
        success = validate_pdf_generation()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Validation failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
