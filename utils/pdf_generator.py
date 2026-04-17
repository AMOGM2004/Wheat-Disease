from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime

def generate_prediction_report(predictions, farmer_name, filename):
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=24, textColor=colors.green)
    story.append(Paragraph("Wheat Disease Prediction Report", title_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Farmer: {farmer_name}", styles['Normal']))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Normal']))
    story.append(Spacer(1, 24))
    
    # Table
    data = [['Date', 'Disease', 'Confidence', 'Stage']]
    for pred in predictions:
        data.append([pred[6], pred[3], f"{pred[4]*100:.1f}%", pred[5]])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.grey),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))
    story.append(table)
    
    doc.build(story)