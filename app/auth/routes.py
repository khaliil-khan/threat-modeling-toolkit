from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from . import auth_bp
from ..models import db, User
from .forms import LoginForm, RegisterForm, ForgotPasswordForm, ResetPasswordForm
from urllib.parse import urljoin, urlparse
from collections import defaultdict, deque
from time import monotonic
import os
from functools import wraps
from flask import session
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


AUTH_RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get('AUTH_RATE_LIMIT_WINDOW_SECONDS', '300'))
LOGIN_RATE_LIMIT_ATTEMPTS = int(os.environ.get('LOGIN_RATE_LIMIT_ATTEMPTS', '5'))
REGISTER_RATE_LIMIT_ATTEMPTS = int(os.environ.get('REGISTER_RATE_LIMIT_ATTEMPTS', '5'))
RESET_RATE_LIMIT_ATTEMPTS = int(os.environ.get('RESET_RATE_LIMIT_ATTEMPTS', '3'))

_login_attempts = defaultdict(deque)
_register_attempts = defaultdict(deque)
_reset_attempts = defaultdict(deque)


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


def send_reset_email(user, reset_token):
    """Send password reset email to user"""
    try:
        smtp_server = os.environ.get('SMTP_SERVER', '').strip()
        smtp_port = os.environ.get('SMTP_PORT', '587').strip()
        sender_email = os.environ.get('SENDER_EMAIL', '').strip()
        sender_password = os.environ.get('SENDER_PASSWORD', '').strip()
        
        reset_url = url_for('auth.reset_password', token=reset_token, _external=True)
        
        subject = 'Password Reset Request - Threat Toolkit'
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; background: #f9f9f9; padding: 20px; border-radius: 8px;">
                    <h2 style="color: #2f81f7;">Password Reset Request</h2>
                    <p>Hello <strong>{user.username}</strong>,</p>
                    <p>You requested to reset your password for your Threat Toolkit account.</p>
                    <p>Click the button below to set a new password:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" style="background-color: #2f81f7; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block;">
                            Reset Password
                        </a>
                    </div>
                    <p style="font-size: 12px; color: #666;">Or copy this link:</p>
                    <p style="font-size: 12px; color: #0066cc; word-break: break-all;"><a href="{reset_url}">{reset_url}</a></p>
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                    <p><strong>⏱️ Important:</strong> This link will expire in <strong>1 hour</strong>.</p>
                    <p style="color: #666;">If you did not request a password reset, please ignore this email. Your account is safe.</p>
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                    <p style="font-size: 12px; color: #999;">
                        <em>Threat Toolkit Security Team</em><br>
                        This is an automated security email. Please do not reply.
                    </p>
                </div>
            </body>
        </html>
        """
        
        text_body = f"""
        Password Reset Request
        
        Hello {user.username},
        
        You requested to reset your password for your Threat Toolkit account.
        
        Click the link below to set a new password:
        {reset_url}
        
        Important: This link will expire in 1 hour.
        
        If you did not request a password reset, please ignore this email. Your account is safe.
        
        Threat Toolkit Security Team
        This is an automated security email. Please do not reply.
        """
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender_email if sender_email else 'Threat Toolkit <noreply@threat-toolkit.local>'
        msg['To'] = user.email
        
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Check if SMTP is properly configured
        if not smtp_server or not sender_email or not sender_password:
            current_app.logger.info(
                'SMTP not configured. Password reset link for user=%s: %s',
                user.username, reset_url
            )
            return 'logged'
        
        try:
            smtp_port = int(smtp_port)
        except ValueError:
            current_app.logger.error(f'Invalid SMTP_PORT: {smtp_port}')
            return False
        
        # Send email via SMTP
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        
        current_app.logger.info(f'✓ Password reset email sent to {user.email}')
        return True
    except smtplib.SMTPAuthenticationError:
        current_app.logger.error(f'✗ SMTP Authentication failed - check email/password')
        return False
    except smtplib.SMTPException as e:
        current_app.logger.error(f'✗ SMTP error: {str(e)}')
        return False
    except Exception as e:
        current_app.logger.error(f'✗ Failed to send reset email: {str(e)}')
        return False


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request password reset"""
    if current_user.is_authenticated:
        return redirect(_default_post_login_redirect())

    client_ip = _client_ip()

    if request.method == 'POST' and _is_rate_limited(
        _reset_attempts,
        client_ip,
        RESET_RATE_LIMIT_ATTEMPTS,
        AUTH_RATE_LIMIT_WINDOW_SECONDS,
    ):
        current_app.logger.warning('rate_limit password_reset ip=%s', client_ip)
        flash('Too many reset attempts. Please try again later.', 'warning')
        return render_template('auth/forgot_password.html', form=ForgotPasswordForm()), 429

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        _record_attempt(_reset_attempts, client_ip, AUTH_RATE_LIMIT_WINDOW_SECONDS)
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            reset_token = user.generate_reset_token()
            db.session.commit()
            result = send_reset_email(user, reset_token)
            if result is False:
                current_app.logger.warning('Email delivery failed for user=%s ip=%s', user.username, client_ip)
            current_app.logger.info('Password reset requested for user=%s ip=%s', user.username, client_ip)
        # Always show same message (don't reveal if email exists)
        flash('If that email is registered, you will receive reset instructions shortly.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('auth/forgot_password.html', form=form)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    if current_user.is_authenticated:
        return redirect(_default_post_login_redirect())
    
    if not token:
        flash('Invalid or expired reset link.', 'danger')
        return redirect(url_for('auth.login'))
    
    # Find user by comparing token hash
    token_hash = User._hash_token(token)
    user = User.query.filter_by(reset_token_hash=token_hash).first()
    if not user:
        flash('Invalid or expired reset link.', 'danger')
        return redirect(url_for('auth.login'))
    
    if not user.verify_reset_token(token):
        flash('Invalid or expired reset link.', 'danger')
        return redirect(url_for('auth.login'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.reset_token_hash = None
        user.reset_token_expiry = None
        db.session.commit()
        current_app.logger.info('Password reset successful for user=%s', user.username)
        flash('Your password has been reset! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password.html', form=form, token=token)


def validate_smtp_config(app):
    """Log SMTP configuration status at startup."""
    smtp_server = os.environ.get('SMTP_SERVER', '').strip()
    sender_email = os.environ.get('SENDER_EMAIL', '').strip()
    sender_password = os.environ.get('SENDER_PASSWORD', '').strip()
    smtp_port = os.environ.get('SMTP_PORT', '587').strip()

    configured = [smtp_server, sender_email, sender_password]

    if not any(configured):
        app.logger.info('SMTP not configured. Email is disabled; console fallback will be used for password resets.')
        return

    missing = []
    if not smtp_server:
        missing.append('SMTP_SERVER')
    if not sender_email:
        missing.append('SENDER_EMAIL')
    if not sender_password:
        missing.append('SENDER_PASSWORD')

    if missing:
        app.logger.warning('SMTP partially configured. Missing variables: %s', ', '.join(missing))

    try:
        int(smtp_port)
    except ValueError:
        app.logger.error('SMTP_PORT contains non-numeric value: %s. SMTP will be treated as unconfigured.', smtp_port)
