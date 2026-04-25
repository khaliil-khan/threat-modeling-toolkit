from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from . import auth_bp
from ..models import db, User
from .forms import LoginForm, RegisterForm
from urllib.parse import urljoin, urlparse
from collections import defaultdict, deque
from time import monotonic
import os
from functools import wraps
from flask import session


AUTH_RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get('AUTH_RATE_LIMIT_WINDOW_SECONDS', '300'))
LOGIN_RATE_LIMIT_ATTEMPTS = int(os.environ.get('LOGIN_RATE_LIMIT_ATTEMPTS', '5'))
REGISTER_RATE_LIMIT_ATTEMPTS = int(os.environ.get('REGISTER_RATE_LIMIT_ATTEMPTS', '5'))

_login_attempts = defaultdict(deque)
_register_attempts = defaultdict(deque)


def _client_ip():
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or 'unknown'


def _prune_attempts(attempts, window_seconds):
    now = monotonic()
    while attempts and (now - attempts[0]) > window_seconds:
        attempts.popleft()
    return now


def _is_rate_limited(store, key, limit, window_seconds):
    attempts = store[key]
    _prune_attempts(attempts, window_seconds)
    return len(attempts) >= limit


def _record_attempt(store, key, window_seconds):
    attempts = store[key]
    now = _prune_attempts(attempts, window_seconds)
    attempts.append(now)


def _is_safe_next_url(target):
    if not target:
        return False
    host_url = urlparse(request.host_url)
    next_url = urlparse(urljoin(request.host_url, target))
    return next_url.scheme in ('http', 'https') and host_url.netloc == next_url.netloc


def _default_post_login_redirect():
    if 'dashboard.index' in current_app.view_functions:
        return url_for('dashboard.index')
    return url_for('auth.profile')


def roles_required(*allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapped(*args, **kwargs):
            user_role = (current_user.role or '').lower()
            normalized_roles = {role.lower() for role in allowed_roles}
            if user_role not in normalized_roles:
                current_app.logger.warning(
                    'rbac denied user=%s role=%s endpoint=%s ip=%s',
                    current_user.username,
                    user_role,
                    request.endpoint,
                    _client_ip(),
                )
                flash('You do not have permission to access that page.', 'danger')
                return redirect(url_for('auth.profile'))
            return view_func(*args, **kwargs)

        return wrapped

    return decorator

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(_default_post_login_redirect())

    client_ip = _client_ip()
    if request.method == 'POST' and _is_rate_limited(
        _register_attempts,
        client_ip,
        REGISTER_RATE_LIMIT_ATTEMPTS,
        AUTH_RATE_LIMIT_WINDOW_SECONDS,
    ):
        current_app.logger.warning('rate_limit register ip=%s', client_ip)
        flash('Too many registration attempts. Please try again later.', 'warning')
        return render_template('auth/register.html', form=RegisterForm()), 429

    form = RegisterForm()
    if form.validate_on_submit():
        admin_emails = {
            email.strip().lower()
            for email in os.environ.get('ADMIN_EMAILS', '').split(',')
            if email.strip()
        }
        role = 'admin' if form.email.data in admin_emails else 'user'
        user = User(username=form.username.data, email=form.email.data, role=role)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        _register_attempts.pop(client_ip, None)
        current_app.logger.info('auth register_success user=%s role=%s ip=%s', user.username, user.role, client_ip)
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        _record_attempt(_register_attempts, client_ip, AUTH_RATE_LIMIT_WINDOW_SECONDS)
        current_app.logger.warning('auth register_failed ip=%s', client_ip)

    return render_template('auth/register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(_default_post_login_redirect())

    client_ip = _client_ip()
    attempted_username = (request.form.get('username') or '').strip().lower()
    rate_limit_key = f'{client_ip}:{attempted_username}'

    if request.method == 'POST' and _is_rate_limited(
        _login_attempts,
        rate_limit_key,
        LOGIN_RATE_LIMIT_ATTEMPTS,
        AUTH_RATE_LIMIT_WINDOW_SECONDS,
    ):
        current_app.logger.warning('rate_limit login username=%s ip=%s', attempted_username, client_ip)
        flash('Too many login attempts. Please try again later.', 'warning')
        return render_template('auth/login.html', form=LoginForm()), 429

    form = LoginForm()
    if form.validate_on_submit():
        normalized_username = (form.username.data or '').strip()
        user = User.query.filter_by(username=normalized_username).first()
        if user and user.check_password(form.password.data):
            session.permanent = True
            login_user(user, remember=form.remember_me.data)
            _login_attempts.pop(rate_limit_key, None)
            current_app.logger.info('auth login_success user=%s ip=%s', user.username, client_ip)
            next_url = request.args.get('next')
            if _is_safe_next_url(next_url):
                return redirect(next_url)
            return redirect(_default_post_login_redirect())
        _record_attempt(_login_attempts, rate_limit_key, AUTH_RATE_LIMIT_WINDOW_SECONDS)
        current_app.logger.warning('auth login_failed username=%s ip=%s', normalized_username, client_ip)
        flash('Invalid username or password.', 'danger')
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    current_app.logger.info('auth logout user=%s ip=%s', current_user.username, _client_ip())
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html')


@auth_bp.route('/admin/users')
@roles_required('admin')
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('auth/admin_users.html', users=users)