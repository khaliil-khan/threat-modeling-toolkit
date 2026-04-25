from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from . import db

class ThreatModel(db.Model):
    __tablename__ = 'threat_models'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    methodology = db.Column(db.String(20), default='STRIDE')
    status = db.Column(db.String(20), default='Active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, default=1)  # temporary, until auth is ready
    threats = db.relationship('Threat', backref='model', lazy=True, cascade='all, delete-orphan')
    dfd_data = db.relationship('DFDData', backref='model', uselist=False, cascade='all, delete-orphan')

class Threat(db.Model):
    __tablename__ = 'threats'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    stride_category = db.Column(db.String(50))
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
