from flask import render_template
from flask_login import login_required, current_user
from sqlalchemy import func
from . import dashboard_bp
from ..models import db, ThreatModel, Threat


@dashboard_bp.route('/')
@login_required
def index():
    total_models = ThreatModel.query.filter_by(user_id=current_user.id).count()

    # Use aggregation queries instead of loading all threats into memory
    base_query = Threat.query.join(ThreatModel).filter(ThreatModel.user_id == current_user.id)

    total_threats = base_query.count()

    # Risk level counts via GROUP BY
    risk_counts = dict(
        db.session.query(Threat.risk_level, func.count(Threat.id))
        .join(ThreatModel)
        .filter(ThreatModel.user_id == current_user.id)
        .group_by(Threat.risk_level)
        .all()
    )
    critical = risk_counts.get('Critical', 0)
    high = risk_counts.get('High', 0)

    # Open threats count
    open_threats = (
        db.session.query(func.count(Threat.id))
        .join(ThreatModel)
        .filter(ThreatModel.user_id == current_user.id, Threat.status == 'Open')
        .scalar() or 0
    )

    # STRIDE category counts via GROUP BY
    stride_rows = (
        db.session.query(Threat.stride_category, func.count(Threat.id))
        .join(ThreatModel)
        .filter(ThreatModel.user_id == current_user.id)
        .group_by(Threat.stride_category)
        .all()
    )
    stride_counts = {cat: count for cat, count in stride_rows if cat}

    # Risk matrix data — only need exploitability, damage, title, risk_level
    matrix_rows = (
        db.session.query(Threat.exploitability, Threat.damage, Threat.title, Threat.risk_level)
        .join(ThreatModel)
        .filter(ThreatModel.user_id == current_user.id)
        .all()
    )
    risk_matrix = [
        {'x': row.exploitability, 'y': row.damage, 'title': row.title, 'level': row.risk_level}
        for row in matrix_rows
    ]

    return render_template(
        'dashboard/index.html',
        total_models=total_models,
        total_threats=total_threats,
        critical=critical,
        high=high,
        open_threats=open_threats,
        stride_counts=stride_counts,
        risk_matrix=risk_matrix,
    )
