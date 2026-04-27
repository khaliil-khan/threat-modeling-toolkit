from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerRangeField, SubmitField
from wtforms.validators import DataRequired, NumberRange

STRIDE_CHOICES = [
    ('Spoofing', 'Spoofing — Impersonating someone/something'),
    ('Tampering', 'Tampering — Modifying data or code'),
    ('Repudiation', 'Repudiation — Denying performed actions'),
    ('Information Disclosure', 'Information Disclosure — Exposing private data'),
    ('Denial of Service', 'Denial of Service — Making system unavailable'),
    ('Elevation of Privilege', 'Elevation of Privilege — Gaining unauthorized access'),
]

PASTA_CHOICES = [
    ('Threat Agent', 'Threat Agent — External actors attempting attacks'),
    ('Attack Vector', 'Attack Vector — Methods used to reach assets'),
    ('Vulnerable Asset', 'Vulnerable Asset — Systems with security weaknesses'),
    ('Technical Impact', 'Technical Impact — Consequences from exploitation'),
    ('Business Impact', 'Business Impact — Damage to business objectives'),
]

class ThreatModelForm(FlaskForm):
    name = StringField('Model Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    methodology = SelectField('Methodology', choices=[('STRIDE', 'STRIDE'), ('PASTA', 'PASTA')])
    submit = SubmitField('Save Threat Model')

class ThreatForm(FlaskForm):
    title = StringField('Threat Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    stride_category = SelectField('STRIDE Category', choices=STRIDE_CHOICES, render_kw={'class': 'form-select'})
    pasta_category = SelectField('PASTA Category', choices=PASTA_CHOICES, render_kw={'class': 'form-select'})
    # DREAD sliders (1-5)
    damage = IntegerRangeField('Damage', validators=[NumberRange(1, 5)], default=1)
    reproducibility = IntegerRangeField('Reproducibility', validators=[NumberRange(1, 5)], default=1)
    exploitability = IntegerRangeField('Exploitability', validators=[NumberRange(1, 5)], default=1)
    affected_users = IntegerRangeField('Affected Users', validators=[NumberRange(1, 5)], default=1)
    discoverability = IntegerRangeField('Discoverability', validators=[NumberRange(1, 5)], default=1)
    countermeasure = TextAreaField('Countermeasure / Mitigation')
    status = SelectField('Status', choices=[('Open', 'Open'), ('Mitigated', 'Mitigated'), ('Accepted', 'Accepted')])
    submit = SubmitField('Save Threat')