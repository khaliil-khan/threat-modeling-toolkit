from flask import render_template, jsonify
from flask_login import login_required, current_user
from . import dashboard_bp
from ..models import ThreatModel, Threat

@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard page with charts"""
    # Basic stats
    total_models = ThreatModel.query.filter_by(user_id=current_user.id).count()
    
    # Get all threats belonging to current user's models
    all_threats = Threat.query.join(ThreatModel).filter(ThreatModel.user_id == current_user.id).all()
    total_threats = len(all_threats)
    critical = sum(1 for t in all_threats if t.risk_level == 'Critical')
    high = sum(1 for t in all_threats if t.risk_level == 'High')
    open_threats = sum(1 for t in all_threats if t.status == 'Open')
    
    # STRIDE category counts for chart
    stride_counts = {}
    for t in all_threats:
        cat = t.stride_category
        stride_counts[cat] = stride_counts.get(cat, 0) + 1
    
    # Prepare risk matrix data points (x = exploitability, y = damage)
    risk_points = [
        {
            'x': t.exploitability,
            'y': t.damage,
            'title': t.title,
            'risk_level': t.risk_level,
            'id': t.id
        }
        for t in all_threats
    ]
    
    return render_template('dashboard/index.html',
                         total_models=total_models,
                         total_threats=total_threats,
                         critical=critical,
                         high=high,
                         open_threats=open_threats,
                         stride_counts=stride_counts,
                         risk_points=risk_points)

@dashboard_bp.route('/api/threats-data')
@login_required
def api_threats_data():
    """JSON endpoint for AJAX chart updates (optional)"""
    all_threats = Threat.query.join(ThreatModel).filter(ThreatModel.user_id == current_user.id).all()
    data = {
        'stride_counts': {},
        'risk_points': []
    }
    for t in all_threats:
        cat = t.stride_category
        data['stride_counts'][cat] = data['stride_counts'].get(cat, 0) + 1
        data['risk_points'].append({
            'x': t.exploitability,
            'y': t.damage,
            'title': t.title,
            'risk': t.risk_level
        })
    return jsonify(data)
