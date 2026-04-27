from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    ROLE_USER = 'user'
    ROLE_ADMIN = 'admin'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default=ROLE_USER, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    threat_models = db.relationship('ThreatModel', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_role(self, *roles):
        normalized = {role.lower() for role in roles}
        return (self.role or '').lower() in normalized

class ThreatModel(db.Model):
    __tablename__ = 'threat_models'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    methodology = db.Column(db.String(20), default='STRIDE')
    status = db.Column(db.String(20), default='Active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    threats = db.relationship('Threat', backref='model', lazy=True, cascade='all, delete-orphan')
    dfd_data = db.relationship('DFDData', backref='model', uselist=False, cascade='all, delete-orphan')

class Threat(db.Model):
    __tablename__ = 'threats'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    stride_category = db.Column(db.String(50))
    pasta_category = db.Column(db.String(50))
    damage = db.Column(db.Integer, default=1)
    reproducibility = db.Column(db.Integer, default=1)
    exploitability = db.Column(db.Integer, default=1)
    affected_users = db.Column(db.Integer, default=1)
    discoverability = db.Column(db.Integer, default=1)
    dread_score = db.Column(db.Float, default=1.0)
    risk_level = db.Column(db.String(20), default='Low')
    countermeasure = db.Column(db.Text)
    status = db.Column(db.String(20), default='Open')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    model_id = db.Column(db.Integer, db.ForeignKey('threat_models.id'), nullable=False)

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
