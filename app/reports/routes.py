from flask import send_file, abort
from flask_login import login_required, current_user
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime
from . import reports_bp
from ..models import ThreatModel

@reports_bp.route('/<int:model_id>/pdf')
@login_required
def generate_pdf(model_id):
    model = ThreatModel.query.get_or_404(model_id)
    if model.user_id != current_user.id:
        abort(403)

    try:
        buffer = BytesIO()
        page_width, page_height = A4
        margin = 0.5 * inch
        
        # Create canvas
        c = canvas.Canvas(buffer, pagesize=A4)
        c.setFont("Helvetica-Bold", 24)
        
        y_position = page_height - margin
        
        # Title
        c.drawString(margin, y_position, "Threat Analysis Report")
        y_position -= 0.3 * inch
        
        # Model information
        c.setFont("Helvetica-Bold", 12)
        c.drawString(margin, y_position, f"Model: {model.name}")
        y_position -= 0.2 * inch
        
        c.setFont("Helvetica", 10)
        c.drawString(margin, y_position, f"Methodology: {model.methodology}")
        y_position -= 0.15 * inch
        
        desc = model.description or "No description"
        if len(desc) > 70:
            desc = desc[:67] + "..."
        c.drawString(margin, y_position, f"Description: {desc}")
        y_position -= 0.15 * inch
        
        c.drawString(margin, y_position, f"Status: {model.status}")
        y_position -= 0.15 * inch
        
        c.drawString(margin, y_position, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        y_position -= 0.3 * inch
        
        # Threats section
        if model.threats:
            c.setFont("Helvetica-Bold", 12)
            c.drawString(margin, y_position, "Identified Threats")
            y_position -= 0.2 * inch
            
            # Table header
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(colors.HexColor('#1F3864'))
            c.rect(margin, y_position - 0.2*inch, page_width - 2*margin, 0.2*inch, fill=1)
            
            c.setFillColor(colors.whitesmoke)
            col1 = margin + 0.1*inch
            col2 = margin + 0.3*inch
            col3 = margin + 2.5*inch
            col4 = margin + 3.8*inch
            col5 = margin + 4.6*inch
            col6 = margin + 5.3*inch
            
            c.drawString(col1, y_position - 0.15*inch, "#")
            c.drawString(col2, y_position - 0.15*inch, "Title")
            c.drawString(col3, y_position - 0.15*inch, "Category")
            c.drawString(col4, y_position - 0.15*inch, "DREAD")
            c.drawString(col5, y_position - 0.15*inch, "Risk")
            c.drawString(col6, y_position - 0.15*inch, "Status")
            
            y_position -= 0.25 * inch
            
            # Table rows
            c.setFont("Helvetica", 9)
            c.setFillColor(colors.black)
            
            for i, t in enumerate(model.threats, 1):
                # Alternate row background
                if i % 2 == 0:
                    c.setFillColor(colors.HexColor('#F5F5F5'))
                    c.rect(margin, y_position - 0.15*inch, page_width - 2*margin, 0.2*inch, fill=1)
                    c.setFillColor(colors.black)
                
                title = (t.title[:20] + "...") if len(t.title) > 20 else t.title
                category = t.stride_category or "N/A"
                dread = f"{t.dread_score}"
                risk = t.risk_level or "N/A"
                status = t.status or "N/A"
                
                c.drawString(col1, y_position - 0.1*inch, str(i))
                c.drawString(col2, y_position - 0.1*inch, title)
                c.drawString(col3, y_position - 0.1*inch, category)
                c.drawString(col4, y_position - 0.1*inch, dread)
                c.drawString(col5, y_position - 0.1*inch, risk)
                c.drawString(col6, y_position - 0.1*inch, status)
                
                y_position -= 0.2 * inch
                
                # Check if we need a new page
                if y_position < margin + 1*inch:
                    c.showPage()
                    y_position = page_height - margin
                    c.setFont("Helvetica", 9)
            
            # Detailed threats on new page
            c.showPage()
            y_position = page_height - margin
            
            c.setFont("Helvetica-Bold", 12)
            c.drawString(margin, y_position, "Threat Details")
            y_position -= 0.3 * inch
            
            for i, t in enumerate(model.threats, 1):
                c.setFont("Helvetica-Bold", 10)
                c.drawString(margin, y_position, f"Threat {i}: {t.title}")
                y_position -= 0.15 * inch
                
                c.setFont("Helvetica", 9)
                
                # Description
                description = t.description or "N/A"
                if len(description) > 60:
                    desc_lines = [description[i:i+60] for i in range(0, len(description), 60)]
                    for line in desc_lines:
                        c.drawString(margin + 0.2*inch, y_position, f"Description: {line}")
                        y_position -= 0.12 * inch
                else:
                    c.drawString(margin + 0.2*inch, y_position, f"Description: {description}")
                    y_position -= 0.12 * inch
                
                category = t.stride_category or "N/A"
                c.drawString(margin + 0.2*inch, y_position, f"Category: {category}")
                y_position -= 0.12 * inch
                
                dread = f"{t.dread_score}"
                c.drawString(margin + 0.2*inch, y_position, f"DREAD Score: {dread}/5.0")
                y_position -= 0.12 * inch
                
                risk = t.risk_level or "N/A"
                c.drawString(margin + 0.2*inch, y_position, f"Risk Level: {risk}")
                y_position -= 0.12 * inch
                
                status = t.status or "N/A"
                c.drawString(margin + 0.2*inch, y_position, f"Status: {status}")
                y_position -= 0.12 * inch
                
                countermeasure = t.countermeasure or "N/A"
                if len(countermeasure) > 60:
                    measure_lines = [countermeasure[i:i+60] for i in range(0, len(countermeasure), 60)]
                    for line in measure_lines:
                        c.drawString(margin + 0.2*inch, y_position, f"Countermeasure: {line}")
                        y_position -= 0.12 * inch
                else:
                    c.drawString(margin + 0.2*inch, y_position, f"Countermeasure: {countermeasure}")
                    y_position -= 0.12 * inch
                
                y_position -= 0.1 * inch
                
                # Check if we need a new page
                if y_position < margin + 1*inch:
                    c.showPage()
                    y_position = page_height - margin
        else:
            c.setFont("Helvetica", 10)
            c.drawString(margin, y_position, "No threats identified yet.")
        
        # Save the PDF
        c.save()
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f'threat_report_{model_id}_{datetime.utcnow().strftime("%Y%m%d")}.pdf',
            mimetype='application/pdf'
        )
    
    except Exception as e:
        print(f'PDF Generation Error: {str(e)}')
        import traceback
        traceback.print_exc()
        abort(500)