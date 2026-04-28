from app import create_app, db
from app.models import User, ThreatModel, Threat

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

    model_stride = ThreatModel(name='STRIDE Model', description='desc', methodology='STRIDE', user_id=user.id)
    db.session.add(model_stride)
    db.session.commit()

    model_dread = ThreatModel(name='DREAD Model', description='desc', methodology='DREAD', user_id=user.id)
    db.session.add(model_dread)
    db.session.commit()

    client = app.test_client()
    client.post('/auth/login', data={'username': 'tester', 'password': 'Testpass1'})

    # Test STRIDE threat save
    print("=== TEST: Save STRIDE Threat ===")
    resp1 = client.post(f'/threats/{model_stride.id}/add-threat', data={
        'title': 'SQL Injection Attack',
        'description': 'Attacker injects SQL code',
        'stride_category': 'Tampering',
        'damage': '5',
        'reproducibility': '4',
        'exploitability': '3',
        'affected_users': '5',
        'discoverability': '2',
        'countermeasure': 'Use parameterized queries',
        'status': 'Open',
    })
    print(f"STRIDE POST status: {resp1.status_code}")
    
    threats_stride = Threat.query.filter_by(model_id=model_stride.id).all()
    print(f"STRIDE threats saved: {len(threats_stride)}")
    if threats_stride:
        t = threats_stride[0]
        print(f"  - Title: {t.title}")
        print(f"  - Category: {t.stride_category}")
        print(f"  - DREAD Score: {t.dread_score}/5")
        print(f"  - Risk Level: {t.risk_level}")

    # Test DREAD threat save
    print("\n=== TEST: Save DREAD Threat ===")
    resp2 = client.post(f'/threats/{model_dread.id}/add-threat', data={
        'title': 'DDoS Attack',
        'description': 'Attacker overloads the server',
        'damage': '5',
        'reproducibility': '3',
        'exploitability': '4',
        'affected_users': '5',
        'discoverability': '4',
        'countermeasure': 'Rate limiting and DDoS protection',
        'status': 'Open',
    })
    print(f"DREAD POST status: {resp2.status_code}")

    threats_dread = Threat.query.filter_by(model_id=model_dread.id).all()
    print(f"DREAD threats saved: {len(threats_dread)}")
    if threats_dread:
        t = threats_dread[0]
        print(f"  - Title: {t.title}")
        print(f"  - DREAD Score: {t.dread_score}/5")
        print(f"  - Risk Level: {t.risk_level}")
        print(f"  - Stride Category (should be None): {t.stride_category}")

    # Test detail page rendering
    print("\n=== TEST: Detail page rendering ===")
    detail_stride = client.get(f'/threats/{model_stride.id}')
    detail_dread = client.get(f'/threats/{model_dread.id}')
    print(f"STRIDE detail status: {detail_stride.status_code}")
    print(f"DREAD detail status: {detail_dread.status_code}")
    print(f"STRIDE has threat row: {'SQL Injection Attack' in detail_stride.get_data(as_text=True)}")
    print(f"DREAD has threat row: {'DDoS Attack' in detail_dread.get_data(as_text=True)}")

    print("\n=== All tests complete ===")
