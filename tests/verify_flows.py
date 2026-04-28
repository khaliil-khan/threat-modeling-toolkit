from app import create_app, db
from app.models import User, ThreatModel, Threat

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

    # Create threat model (STRIDE)
    m = ThreatModel(name='Test Model', description='For verification', methodology='STRIDE', user_id=u.id)
    db.session.add(m)
    db.session.commit()

    # Add threat
    t = Threat(
        title='Test Threat',
        description='Example threat',
        stride_category='Spoofing',
        damage=5,
        reproducibility=4,
        exploitability=3,
        affected_users=2,
        discoverability=1,
        countermeasure='Apply fix',
        status='Open',
        model_id=m.id,
    )
    t.calculate_dread()
    db.session.add(t)
    db.session.commit()

    # Verify values
    print('DREAD score:', t.dread_score)
    print('Risk level:', t.risk_level)

    # Use test client to GET the model detail page (requires login)
    client = app.test_client()
    # Log in using the login form (CSRF disabled in test config)
    resp_login = client.post('/auth/login', data={'username': 'testuser', 'password': 'Testpass1'}, follow_redirects=True)
    print('Login POST status:', resp_login.status_code)
    resp = client.get(f'/threats/{m.id}')
    print('GET /threats/{id} status:', resp.status_code)
    if resp.status_code != 200:
        print('Detail page content (truncated):')
        print(resp.get_data(as_text=True)[:1000])

print('Verification script completed')
