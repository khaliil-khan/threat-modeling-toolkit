from flask import redirect, url_for, current_app
from flask_login import current_user
from . import dashboard_bp


@dashboard_bp.route('/')
def index():
if current_user.is_authenticated:
if 'threats.list_models' in current_app.view_functions:
return redirect(url_for('threats.list_models'))
return redirect(url_for('auth.profile'))
return redirect(url_for('auth.login'))
