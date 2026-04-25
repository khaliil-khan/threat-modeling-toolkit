from flask import render_template, jsonify
from . import dashboard_bp
from ..models import ThreatModel, Threat

@dashboard_bp.route('/')
def index():
    """Main dashboard page with charts"""
    all_threats = Threat.query.all()
    total_models = ThreatModel.query.count()
    total_threats = len(all_threats)
    critical = sum(1 for t in all_threats if t.risk_level == 'Critical')
    high = sum(1 for t in all_threats if t.risk_level == 'High')
    open_threats = sum(1 for t in all_threats if t.status == 'Open')

    stride_counts = {}
    for t in all_threats:
        cat = t.stride_category
        stride_counts[cat] = stride_counts.get(cat, 0) + 1

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
def api_threats_data():
    all_threats = Threat.query.all()
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

@dashboard_bp.route('/api/recent-threats')
def api_recent_threats():
    threats = Threat.query.order_by(Threat.dread_score.desc()).limit(10).all()
    return jsonify({
        'threats': [{
            'title': t.title,
            'stride_category': t.stride_category,
            'dread_score': t.dread_score,
            'risk_level': t.risk_level
        } for t in threats]
    })
