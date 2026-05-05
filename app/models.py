from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import hashlib
import secrets
import os

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    ROLE_USER = 'user'
    ROLE_ADMIN = 'admin'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default=ROLE_USER, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    reset_token_hash = db.Column(db.String(256), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    threat_models = db.relationship('ThreatModel', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, *roles):
        normalized = {role.lower() for role in roles}
        return (self.role or '').lower() in normalized

    @staticmethod
    def _hash_token(token):
        """Hash a token for secure storage using SHA-256."""
        return hashlib.sha256(token.encode('utf-8')).hexdigest()

    def generate_reset_token(self):
        """Generate a password reset token valid for 1 hour.
        
        Returns the raw token (to be sent via email). Only the hash is stored in DB.
        """
        secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')
        serializer = URLSafeTimedSerializer(secret_key)
        raw_token = serializer.dumps(self.email, salt='password-reset')
        self.reset_token_hash = self._hash_token(raw_token)
        self.reset_token_expiry = datetime.utcnow() + timedelta(hours=1)
        return raw_token

    def verify_reset_token(self, token):
        """Verify reset token and return email if valid."""
        if not token or not self.reset_token_hash or not self.reset_token_expiry:
            return None

        # Check expiry FIRST (prevents timing attacks)
        if datetime.utcnow() > self.reset_token_expiry:
            self.reset_token_hash = None
            self.reset_token_expiry = None
            db.session.commit()
            return None

        # Compare hashes (constant-time via hmac.compare_digest)
        import hmac
        token_hash = self._hash_token(token)
        if not hmac.compare_digest(token_hash, self.reset_token_hash):
            return None

        # Verify token signature
        secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')
        serializer = URLSafeTimedSerializer(secret_key)
        try:
            email = serializer.loads(token, salt='password-reset', max_age=3600)
            return email if email == self.email else None
        except (SignatureExpired, BadSignature):
            return None

class ThreatModel(db.Model):
    __tablename__ = 'threat_models'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    methodology = db.Column(db.String(20), default='STRIDE')
    status = db.Column(db.String(20), default='Active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    threats = db.relationship('Threat', backref='model', lazy=True, cascade='all, delete-orphan')
    dfd_data = db.relationship('DFDData', backref='model', uselist=False, cascade='all, delete-orphan')

class Threat(db.Model):
    __tablename__ = 'threats'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    stride_category = db.Column(db.String(50), index=True)
    damage = db.Column(db.Integer, default=1)
    reproducibility = db.Column(db.Integer, default=1)
    exploitability = db.Column(db.Integer, default=1)
    affected_users = db.Column(db.Integer, default=1)
    discoverability = db.Column(db.Integer, default=1)
    dread_score = db.Column(db.Float, default=1.0)
    risk_level = db.Column(db.String(20), default='Low', index=True)
    countermeasure = db.Column(db.Text)
    status = db.Column(db.String(20), default='Open', index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    model_id = db.Column(db.Integer, db.ForeignKey('threat_models.id'), nullable=False, index=True)

    def calculate_dread(self):
        self.dread_score = round((self.damage + self.reproducibility +
                                  self.exploitability + self.affected_users +
                                  self.discoverability) / 5, 2)
        if self.dread_score >= 4:
            self.risk_level = 'Critical'
        elif self.dread_score >= 3:
            self.risk_level = 'High'
        elif self.dread_score >= 2:
            self.risk_level = 'Medium'
        else:
            self.risk_level = 'Low'

class DFDData(db.Model):
    __tablename__ = 'dfd_data'
    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('threat_models.id'), nullable=False)
    canvas_json = db.Column(db.Text, default='{}')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
