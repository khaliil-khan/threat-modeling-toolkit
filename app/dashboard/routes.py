from flask import render_template
from flask_login import current_user, login_required
from ..models import ThreatModel, Threat
from . import dashboard_bp


@dashboard_bp.route('/')
@login_required
def index():
    model_ids_query = ThreatModel.query.with_entities(ThreatModel.id).filter_by(user_id=current_user.id)
    model_ids = [row.id for row in model_ids_query.all()]

    total_models = len(model_ids)
    if model_ids:
        threats = Threat.query.filter(Threat.model_id.in_(model_ids)).all()
    else:
        threats = []

    total_threats = len(threats)
    critical = sum(1 for threat in threats if threat.risk_level == 'Critical')
    open_threats = sum(1 for threat in threats if threat.status == 'Open')

    return render_template(
        'dashboard/index.html',
        total_models=total_models,
        total_threats=total_threats,
        critical=critical,
        open_threats=open_threats,
    )
