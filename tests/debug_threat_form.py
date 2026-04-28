from app import create_app, db
from app.models import User, ThreatModel
from app.threats.forms import ThreatForm
from flask_wtf import FlaskForm

app = create_app()
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

with app.app_context():
    db.drop_all()
    db.create_all()

    user = User(username='tester', email='tester@example.com', role='user')
    user.set_password('Testpass1')
    db.session.add(user)
    db.session.commit()

    # Test with STRIDE model
    model_stride = ThreatModel(name='STRIDE Model', description='desc', methodology='STRIDE', user_id=user.id)
    db.session.add(model_stride)
    db.session.commit()

    # Test with DREAD model
    model_dread = ThreatModel(name='DREAD Model', description='desc', methodology='DREAD', user_id=user.id)
    db.session.add(model_dread)
    db.session.commit()

    client = app.test_client()
    login_resp = client.post('/auth/login', data={'username': 'tester', 'password': 'Testpass1'}, follow_redirects=False)

    # Test 1: GET the add-threat page and check form rendering
    print("=== TEST 1: Check rendered form for STRIDE ===")
    get_resp = client.get(f'/threats/{model_stride.id}/add-threat')
    page_html = get_resp.get_data(as_text=True)
    print(f"GET status: {get_resp.status_code}")
    print(f"Has 'title' field: {'name=\"title\"' in page_html or 'id=\"title\"' in page_html}")
    print(f"Has 'stride_category' field: {'stride_category' in page_html}")
    print(f"Has 'damage' field: {'damage' in page_html}")
    print(f"Has 'reproducibility' field: {'reproducibility' in page_html}")
    print(f"Has 'exploitability' field: {'exploitability' in page_html}")
    print(f"Has 'affected_users' field: {'affected_users' in page_html}")
    print(f"Has 'discoverability' field: {'discoverability' in page_html}")
    print(f"Has 'status' field: {'status' in page_html}")
    print(f"Has 'countermeasure' field: {'countermeasure' in page_html}")
    print(f"Has form tag: {'<form' in page_html}")
    print(f"Has csrf_token: {'csrf_token' in page_html}")

    # Test 2: POST with minimal valid data for STRIDE
    print("\n=== TEST 2: POST STRIDE threat with all required fields ===")
    post_data = {
        'title': 'Test Threat',
        'description': 'Threat description here',
        'stride_category': 'Spoofing',
        'damage': '3',
        'reproducibility': '3',
        'exploitability': '3',
        'affected_users': '3',
        'discoverability': '3',
        'countermeasure': 'Apply mitigation',
        'status': 'Open',
    }
    post_resp = client.post(f'/threats/{model_stride.id}/add-threat', data=post_data, follow_redirects=False)
    print(f"POST status: {post_resp.status_code}")
    print(f"Redirect location: {post_resp.headers.get('Location', 'NO REDIRECT')}")
    
    # Test 3: POST with DREAD model (no stride_category)
    print("\n=== TEST 3: POST DREAD threat ===")
    get_resp2 = client.get(f'/threats/{model_dread.id}/add-threat')
    page_html2 = get_resp2.get_data(as_text=True)
    print(f"DREAD GET status: {get_resp2.status_code}")
    print(f"Has DREAD note: {'DREAD methodology' in page_html2}")
    
    post_data_dread = {
        'title': 'DREAD Threat',
        'description': 'DREAD threat desc',
        'damage': '5',
        'reproducibility': '4',
        'exploitability': '3',
        'affected_users': '2',
        'discoverability': '1',
        'countermeasure': 'Fix now',
        'status': 'Open',
    }
    post_resp2 = client.post(f'/threats/{model_dread.id}/add-threat', data=post_data_dread, follow_redirects=False)
    print(f"DREAD POST status: {post_resp2.status_code}")
    print(f"DREAD redirect: {post_resp2.headers.get('Location', 'NO REDIRECT')}")

    # Test 4: Test form validation directly
    print("\n=== TEST 4: Form validation (STRIDE) ===")
    with app.test_request_context(f'/threats/{model_stride.id}/add-threat', method='POST', data=post_data):
        form = ThreatForm()
        is_valid = form.validate()
        print(f"Form valid: {is_valid}")
        if not is_valid:
            print(f"Form errors: {form.errors}")
        print(f"Form fields: {[f.name for f in form]}")

    print("\n=== All tests complete ===")
