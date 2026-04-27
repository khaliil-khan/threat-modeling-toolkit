from flask import send_file, abort
from flask_login import login_required, current_user
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from . import reports_bp
from ..models import ThreatModel

@reports_bp.route('/<int:model_id>/pdf')
@login_required
def generate_pdf(model_id):
    model = ThreatModel.query.get_or_404(model_id)
    if model.user_id != current_user.id:
        abort(403)

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f'Threat Analysis Report: {model.name}', styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f'Methodology: {model.methodology}', styles['Normal']))
    story.append(Paragraph(f'Generated: {model.created_at.strftime("%Y-%m-%d")}', styles['Normal']))
    story.append(Spacer(1, 20))

    data = [['#', 'Title', 'STRIDE', 'DREAD', 'Risk', 'Status']]
    for i, t in enumerate(model.threats, 1):
        data.append([str(i), t.title, t.stride_category, str(t.dread_score), t.risk_level, t.status])

    table = Table(data, colWidths=[30, 150, 100, 50, 60, 70])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1F3864')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F2F2F2')]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    story.append(table)
    doc.build(story)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True,
                     download_name=f'threat_report_{model_id}.pdf',
                     mimetype='application/pdf')