import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, ThreatModel, Threat

app = create_app()
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

with app.app_context():
    db.drop_all()
    db.create_all()
    
    # Create user 1
    u1 = User(username='user1', email='user1@example.com', role='user')
    u1.set_password('Pass1')
    db.session.add(u1)
    db.session.commit()
    
    # Create user 2
    u2 = User(username='user2', email='user2@example.com', role='user')
    u2.set_password('Pass2')
    db.session.add(u2)
    db.session.commit()
    
    # User 1 creates a model
    m1 = ThreatModel(name='User 1 Model', description='Model by user 1', methodology='STRIDE', user_id=u1.id)
    db.session.add(m1)
    db.session.commit()
    
    print(f'User 1 model: ID={m1.id}, user_id={m1.user_id}')
    
    # User 2 creates a model
    m2 = ThreatModel(name='User 2 Model', description='Model by user 2', methodology='STRIDE', user_id=u2.id)
    db.session.add(m2)
    db.session.commit()
    
    print(f'User 2 model: ID={m2.id}, user_id={m2.user_id}')
    
    client = app.test_client()
    
    print('\n--- Test 1: User 1 accesses own model ---')
    client.post('/auth/login', data={'username': 'user1', 'password': 'Pass1'})
    resp = client.get(f'/reports/{m1.id}/pdf')
    print(f'User 1 accessing own model (ID={m1.id}): {resp.status_code}')
    assert resp.status_code == 200, 'Should have access'
    
    print('\n--- Test 2: User 1 tries to access User 2 model ---')
    resp = client.get(f'/reports/{m2.id}/pdf')
    print(f'User 1 accessing User 2 model (ID={m2.id}): {resp.status_code}')
    if resp.status_code != 403:
        print(f'ERROR: Expected 403, got {resp.status_code}')
        print(f'Response data: {resp.get_data(as_text=True)[:200]}')
    else:
        print('✓ Authorization check passed!')
    
    print('\n--- Test 3: User 2 accesses own model ---')
    client.get('/auth/logout')
    client.post('/auth/login', data={'username': 'user2', 'password': 'Pass2'})
    resp = client.get(f'/reports/{m2.id}/pdf')
    print(f'User 2 accessing own model (ID={m2.id}): {resp.status_code}')
    assert resp.status_code == 200, 'Should have access'
    
    print('\n--- Test 4: User 2 tries to access User 1 model ---')
    resp = client.get(f'/reports/{m1.id}/pdf')
    print(f'User 2 accessing User 1 model (ID={m1.id}): {resp.status_code}')
    if resp.status_code != 403:
        print(f'ERROR: Expected 403, got {resp.status_code}')
    else:
        print('✓ Authorization check passed!')
    
    print('\n--- Test 5: Unauthenticated access ---')
    client.get('/auth/logout')
    resp = client.get(f'/reports/{m1.id}/pdf')
    print(f'Unauthenticated access to model: {resp.status_code}')
    assert resp.status_code == 302, 'Should redirect to login'
    print('✓ Redirected to login page')

print('\n✅ All authorization tests completed!')
