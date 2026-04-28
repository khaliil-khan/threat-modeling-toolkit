import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User, ThreatModel, Threat

app = create_app()
app.config['TESTING'] = True

with app.app_context():
    db.drop_all()
    db.create_all()
    
    m = ThreatModel(name='Test', description='Test', methodology='STRIDE', user_id=1)
    db.session.add(m)
    db.session.commit()
    
    threats = [
        Threat(damage=5, reproducibility=2, exploitability=2, affected_users=5, discoverability=2, model_id=m.id),
        Threat(damage=5, reproducibility=3, exploitability=4, affected_users=5, discoverability=3, model_id=m.id),
        Threat(damage=5, reproducibility=2, exploitability=3, affected_users=4, discoverability=2, model_id=m.id),
    ]
    
    for t in threats:
        t.calculate_dread()
        db.session.add(t)
    
    db.session.commit()
    
    for t in Threat.query.all():
        print(f'DREAD: {t.dread_score}')
