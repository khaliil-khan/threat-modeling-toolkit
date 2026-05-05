
from datetime import datetime
import json
from flask import render_template, request, abort, jsonify, current_app
from flask_login import login_required, current_user
from . import dfd_bp
from ..models import db, ThreatModel, DFDData

# Maximum allowed size for DFD canvas JSON (512 KB)
MAX_CANVAS_JSON_SIZE = 512 * 1024


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

    # Validate canvas JSON size
    if len(canvas_json) > MAX_CANVAS_JSON_SIZE:
        return jsonify({'status': 'error', 'message': 'Canvas data too large (max 512KB).'}), 413

    # Validate it's actually valid JSON
    try:
        parsed = json.loads(canvas_json)
        if not isinstance(parsed, (list, dict)):
            return jsonify({'status': 'error', 'message': 'Canvas data must be a JSON array or object.'}), 400
    except (json.JSONDecodeError, TypeError):
        return jsonify({'status': 'error', 'message': 'Invalid JSON in canvas data.'}), 400

    dfd_data = model.dfd_data or DFDData(model_id=model.id)
    dfd_data.canvas_json = canvas_json
    dfd_data.updated_at = datetime.utcnow()
    db.session.add(dfd_data)
    db.session.commit()

    return jsonify({'status': 'saved'})
