# Originally designed by Waleed Ahmad (Threat Management Module)
from flask import render_template, redirect, url_for, flash, request, abort, jsonify
from flask_login import login_required, current_user
from . import threats_bp
from ..models import db, ThreatModel, Threat
from .forms import ThreatModelForm, ThreatForm
from ..utils.threat_analytics import ThreatAnalytics, ThreatFilter, ThreatReporter

# List all threat models for current user
@threats_bp.route('/')
@login_required
def list_models():
    models = ThreatModel.query.filter_by(user_id=current_user.id).all()
    return render_template('threats/list.html', models=models)

# Create new threat model
@threats_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_model():
    form = ThreatModelForm()
    if form.validate_on_submit():
        model = ThreatModel(
            name=form.name.data,
            description=form.description.data,
            methodology=form.methodology.data,
            user_id=current_user.id
        )
        db.session.add(model)
        db.session.commit()
        flash('Threat model created!', 'success')
        return redirect(url_for('threats.model_detail', model_id=model.id))
    return render_template('threats/create.html', form=form)

# View model details and its threats
@threats_bp.route('/<int:model_id>')
@login_required
def model_detail(model_id):
    model = ThreatModel.query.get_or_404(model_id)
    if model.user_id != current_user.id:
        abort(403)
    return render_template('threats/detail.html', model=model)

# Add a threat to a model
@threats_bp.route('/<int:model_id>/add-threat', methods=['GET', 'POST'])
@login_required
def add_threat(model_id):
    model = ThreatModel.query.get_or_404(model_id)
    if model.user_id != current_user.id:
        abort(403)
    form = ThreatForm()
    if form.validate_on_submit():
        threat = Threat(
            title=form.title.data,
            description=form.description.data,
            stride_category=form.stride_category.data if model.methodology == 'STRIDE' else None,
            damage=form.damage.data,
            reproducibility=form.reproducibility.data,
            exploitability=form.exploitability.data,
            affected_users=form.affected_users.data,
            discoverability=form.discoverability.data,
            countermeasure=form.countermeasure.data,
            status=form.status.data,
            model_id=model_id
        )
        threat.calculate_dread()  # Auto-calculate score and risk level
        db.session.add(threat)
        db.session.commit()
        flash('Threat added!', 'success')
        return redirect(url_for('threats.model_detail', model_id=model_id, _anchor='identified-threats'))
    return render_template('threats/add_threat.html', form=form, model=model)

# Delete threat model
@threats_bp.route('/<int:model_id>/delete', methods=['POST'])
@login_required
def delete_model(model_id):
    model = ThreatModel.query.get_or_404(model_id)
    if model.user_id != current_user.id:
        abort(403)
    db.session.delete(model)
    db.session.commit()
    flash('Threat model deleted.', 'info')
    return redirect(url_for('threats.list_models'))


# ============================================================================
# ANALYTICS AND REPORTING ENDPOINTS (Added by Waleed Ahmad - May 2026)
# ============================================================================

@threats_bp.route('/<int:model_id>/analytics')
@login_required
def get_analytics(model_id):
    """Get comprehensive threat analytics for a model"""
    model = ThreatModel.query.get_or_404(model_id)
    if model.user_id != current_user.id:
        abort(403)
    
    analytics = ThreatAnalytics.get_threat_statistics(current_user.id)
    risk_grouped = ThreatAnalytics.get_threat_by_risk_level(model_id, current_user.id)
    stride_grouped = ThreatAnalytics.get_threat_by_stride(model_id, current_user.id)
    
    return render_template('threats/analytics.html', 
                         model=model,
                         analytics=analytics,
                         risk_grouped=risk_grouped,
                         stride_grouped=stride_grouped)


@threats_bp.route('/<int:model_id>/analytics/json')
@login_required
def get_analytics_json(model_id):
    """Get threat analytics as JSON"""
    model = ThreatModel.query.get_or_404(model_id)
    if model.user_id != current_user.id:
        abort(403)
    
    analytics = ThreatAnalytics.get_threat_statistics(current_user.id)
    risk_grouped = ThreatAnalytics.get_threat_by_risk_level(model_id, current_user.id)
    stride_grouped = ThreatAnalytics.get_threat_by_stride(model_id, current_user.id)
    
    return jsonify({
        'model_id': model_id,
        'model_name': model.name,
        'analytics': analytics,
        'risk_distribution': {k: len(v) for k, v in risk_grouped.items()},
        'stride_distribution': {k: len(v) for k, v in stride_grouped.items()}
    })


@threats_bp.route('/<int:model_id>/search', methods=['GET', 'POST'])
@login_required
def search_threats(model_id):
    """Search and filter threats in a model"""
    model = ThreatModel.query.get_or_404(model_id)
    if model.user_id != current_user.id:
        abort(403)
    
    search_term = request.args.get('q', '')
    filters = {}
    
    # Build filter dictionary from query parameters
    if request.args.get('risk_level'):
        filters['risk_level'] = request.args.getlist('risk_level')
    if request.args.get('status'):
        filters['status'] = request.args.getlist('status')
    if request.args.get('stride_category'):
        filters['stride_category'] = request.args.getlist('stride_category')
    if request.args.get('min_dread'):
        try:
            filters['min_dread_score'] = float(request.args.get('min_dread'))
        except ValueError:
            pass
    if request.args.get('max_dread'):
        try:
            filters['max_dread_score'] = float(request.args.get('max_dread'))
        except ValueError:
            pass
    
    threats = ThreatFilter.search_threats(model_id, current_user.id, search_term, filters)
    
    return render_template('threats/search_results.html',
                         model=model,
                         threats=threats,
                         search_term=search_term,
                         filters=filters)


@threats_bp.route('/<int:model_id>/filter', methods=['POST'])
@login_required
def filter_threats(model_id):
    """Filter threats via POST request (returns JSON)"""
    model = ThreatModel.query.get_or_404(model_id)
    if model.user_id != current_user.id:
        abort(403)
    
    filters = request.get_json() or {}
    query = Threat.query.filter_by(model_id=model_id)
    filtered_threats = ThreatFilter.filter_threats(query, filters).all()
    
    return jsonify({
        'count': len(filtered_threats),
        'threats': [
            {
                'id': t.id,
                'title': t.title,
                'risk_level': t.risk_level,
                'dread_score': t.dread_score,
                'status': t.status,
                'stride_category': t.stride_category
            }
            for t in filtered_threats
        ]
    })


@threats_bp.route('/<int:model_id>/report/json')
@login_required
def export_report_json(model_id):
    """Export threat model as JSON report"""
    model = ThreatModel.query.get_or_404(model_id)
    if model.user_id != current_user.id:
        abort(403)
    
    report = ThreatReporter.generate_json_report(model_id, current_user.id)
    if not report:
        abort(403)
    
    return jsonify({'report': report})


@threats_bp.route('/<int:model_id>/report/text')
@login_required
def export_report_text(model_id):
    """Export threat model as text report"""
    model = ThreatModel.query.get_or_404(model_id)
    if model.user_id != current_user.id:
        abort(403)
    
    report = ThreatReporter.generate_summary_report(model_id, current_user.id)
    if not report:
        abort(403)
    
    return report, 200, {'Content-Type': 'text/plain', 'Content-Disposition': f'attachment; filename="threat_report_{model_id}.txt"'}


@threats_bp.route('/<int:model_id>/report/download')
@login_required
def download_report(model_id):
    """Download comprehensive threat report"""
    model = ThreatModel.query.get_or_404(model_id)
    if model.user_id != current_user.id:
        abort(403)
    
    report = ThreatReporter.generate_summary_report(model_id, current_user.id)
    if not report:
        abort(403)
    
    from flask import send_file
    from io import BytesIO
    
    report_bytes = BytesIO(report.encode('utf-8'))
    report_bytes.seek(0)
    
    return send_file(
        report_bytes,
        mimetype='text/plain',
        as_attachment=True,
        download_name=f'threat_report_{model_id}_{ThreatReporter._get_timestamp()}.txt'
    )


@threats_bp.route('/<int:model_id>/export/csv')
@login_required
def export_csv(model_id):
    """Export threat model as CSV"""
    model = ThreatModel.query.get_or_404(model_id)
    if model.user_id != current_user.id:
        abort(403)
    
    csv_data = ThreatReporter.generate_csv_export(model_id, current_user.id)
    if not csv_data:
        abort(403)
    
    from flask import send_file
    from io import BytesIO
    
    csv_bytes = BytesIO(csv_data.encode('utf-8'))
    csv_bytes.seek(0)
    
    return send_file(
        csv_bytes,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'threats_{model_id}_{_get_report_timestamp()}.csv'
    )


@threats_bp.route('/<int:model_id>/report/executive-summary')
@login_required
def executive_summary(model_id):
    """Get executive summary report"""
    model = ThreatModel.query.get_or_404(model_id)
    if model.user_id != current_user.id:
        abort(403)
    
    summary = ThreatReporter.generate_executive_summary(model_id, current_user.id)
    if not summary:
        abort(403)
    
    return summary, 200, {'Content-Type': 'text/plain'}


# Helper method for timestamped reports
def _get_report_timestamp():
    """Get formatted timestamp for report filenames"""
    from datetime import datetime
    return datetime.utcnow().strftime('%Y%m%d_%H%M%S')
