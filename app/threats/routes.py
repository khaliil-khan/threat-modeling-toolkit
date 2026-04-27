from flask import render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user
from . import threats_bp
from ..models import db, ThreatModel, Threat
from .forms import ThreatModelForm, ThreatForm

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
            pasta_category=form.pasta_category.data if model.methodology == 'PASTA' else None,
            dread_category=form.dread_category.data if model.methodology == 'DREAD' else None,
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
        return redirect(url_for('threats.model_detail', model_id=model_id))
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