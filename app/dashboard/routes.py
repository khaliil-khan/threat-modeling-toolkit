from flask import render_template, jsonify
from flask_login import login_required, current_user
from . import dashboard_bp
from ..models import ThreatModel, Threat

@dashboard_bp.route('/')
@login_required
def index():
    total_models = ThreatModel.query.filter_by(user_id=current_user.id).count()
    all_threats = Threat.query.join(ThreatModel).filter(ThreatModel.user_id == current_user.id).all()
    total_threats = len(all_threats)
    critical = sum(1 for t in all_threats if t.risk_level == 'Critical')
    high = sum(1 for t in all_threats if t.risk_level == 'High')
    open_threats = sum(1 for t in all_threats if t.status == 'Open')

    stride_counts = {}
    for t in all_threats:
        stride_counts[t.stride_category] = stride_counts.get(t.stride_category, 0) + 1

    risk_matrix = [{'x': t.exploitability, 'y': t.damage, 'title': t.title, 'level': t.risk_level}
                   for t in all_threats]

    return render_template('dashboard/index.html',
                           total_models=total_models, total_threats=total_threats,
                           critical=critical, high=high, open_threats=open_threats,
                           stride_counts=stride_counts, risk_matrix=risk_matrix)