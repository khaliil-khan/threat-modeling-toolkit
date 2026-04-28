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

    model = ThreatModel(name='Model 1', description='desc', methodology='STRIDE', user_id=user.id)
    db.session.add(model)
    db.session.commit()

    client = app.test_client()
    login_resp = client.post('/auth/login', data={'username': 'tester', 'password': 'Testpass1'}, follow_redirects=False)
    print('login_status', login_resp.status_code)

    post_data = {
        'title': 'Threat A',
        'description': 'Threat desc',
        'stride_category': 'Spoofing',
        'damage': '5',
        'reproducibility': '4',
        'exploitability': '3',
        'affected_users': '2',
        'discoverability': '1',
        'countermeasure': 'Mitigate it',
        'status': 'Open',
    }
    resp = client.post(f'/threats/{model.id}/add-threat', data=post_data, follow_redirects=False)
    print('add_threat_status', resp.status_code)
    print('location', resp.headers.get('Location'))
    print('body_prefix', resp.get_data(as_text=True)[:500])

    threats = Threat.query.filter_by(model_id=model.id).all()
    print('threat_count', len(threats))
    if threats:
        t = threats[0]
        print('saved_score', t.dread_score)
        print('saved_risk', t.risk_level)
