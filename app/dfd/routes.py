
from datetime import datetime
from flask import render_template, request, abort, jsonify
from flask_login import login_required, current_user
from . import dfd_bp
from ..models import db, ThreatModel, DFDData

@dfd_bp.route('/<int:model_id>/edit', methods=['GET'])
@login_required
def edit_dfd(model_id):
    model = ThreatModel.query.get_or_404(model_id)
    if model.user_id != current_user.id:
        abort(403)
    return render_template('dfd/editor.html', model=model)

@dfd_bp.route('/<int:model_id>/save', methods=['POST'])
@login_required
def save_dfd(model_id):
    model = ThreatModel.query.get_or_404(model_id)
    if model.user_id != current_user.id:
        abort(403)

    if not request.is_json:
        return jsonify({'status': 'error', 'message': 'Expected JSON payload.'}), 400

    data = request.get_json(silent=True) or {}
    canvas_json = data.get('canvas_json') or '{}'

    dfd_data = model.dfd_data or DFDData(model_id=model.id)
    dfd_data.canvas_json = canvas_json
    dfd_data.updated_at = datetime.utcnow()
    db.session.add(dfd_data)
    db.session.commit()

    return jsonify({'status': 'saved'})
