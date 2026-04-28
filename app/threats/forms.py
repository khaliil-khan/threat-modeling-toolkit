from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, IntegerRangeField, SubmitField
from wtforms.validators import DataRequired, NumberRange, Optional

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

DREAD_CHOICES = [
    ('Damage Potential', 'Damage Potential — Potential loss from exploitation'),
    ('Reproducibility', 'Reproducibility — Ease of reproducing the attack'),
    ('Exploitability', 'Exploitability — Skill/effort required to exploit'),
    ('Affected Users', 'Affected Users — Number of users impacted'),
    ('Discoverability', 'Discoverability — Likelihood threat will be discovered'),
]

class ThreatModelForm(FlaskForm):
    name = StringField('Model Name', validators=[DataRequired()])
    description = TextAreaField('Description')
    methodology = SelectField('Methodology', choices=[('STRIDE', 'STRIDE'), ('PASTA', 'PASTA'), ('DREAD', 'DREAD')])
    submit = SubmitField('Save Threat Model')

class ThreatForm(FlaskForm):
    title = StringField('Threat Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    stride_category = SelectField('STRIDE Category', choices=STRIDE_CHOICES, validators=[Optional()], render_kw={'class': 'form-select'})
    # DREAD sliders (1-5)
    damage = IntegerRangeField('Damage', validators=[NumberRange(1, 5)], default=1)
    reproducibility = IntegerRangeField('Reproducibility', validators=[NumberRange(1, 5)], default=1)
    exploitability = IntegerRangeField('Exploitability', validators=[NumberRange(1, 5)], default=1)
    affected_users = IntegerRangeField('Affected Users', validators=[NumberRange(1, 5)], default=1)
    discoverability = IntegerRangeField('Discoverability', validators=[NumberRange(1, 5)], default=1)
    countermeasure = TextAreaField('Countermeasure / Mitigation')
    status = SelectField('Status', choices=[('Open', 'Open'), ('Mitigated', 'Mitigated'), ('Accepted', 'Accepted')])
    submit = SubmitField('Save Threat')