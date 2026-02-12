"""
Report Generator Module
Generates downloadable PDF reports with performance analysis and suggestions.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.graphics.shapes import Drawing, Line
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from io import BytesIO
from datetime import datetime
from typing import Dict, List


def generate_assessment_report(
    performance_data: Dict,
    questions_history: List[Dict],
    improvement_suggestions: str,
    content_title: str = "Assessment Report"
) -> bytes:
    """
    Generate a comprehensive PDF assessment report.
    
    Args:
        performance_data: Dict with performance metrics
        questions_history: List of question results
        improvement_suggestions: AI-generated suggestions
        content_title: Title for the report
        
    Returns:
        bytes: PDF file content
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, 
        pagesize=A4,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        textColor=colors.HexColor('#1a365d'),
        alignment=1  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        spaceBefore=20,
        spaceAfter=12,
        textColor=colors.HexColor('#2c5282')
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubheading',
        parent=styles['Heading3'],
        fontSize=12,
        spaceBefore=15,
        spaceAfter=8,
        textColor=colors.HexColor('#4a5568')
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=8,
        leading=14
    )
    
    # Build content
    story = []
    
    # Title
    story.append(Paragraph("📚 Adaptive Assessment Report", title_style))
    story.append(Paragraph(
        f"Generated on: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}",
        ParagraphStyle('Date', parent=normal_style, alignment=1, textColor=colors.gray)
    ))
    story.append(Spacer(1, 30))
    
    # Performance Summary Section
    story.append(Paragraph("📊 Performance Summary", heading_style))
    
    # Create performance metrics table
    total_q = performance_data.get('total_questions', 0)
    correct = performance_data.get('correct_answers', 0)
    incorrect = total_q - correct
    accuracy = performance_data.get('accuracy', 0)
    avg_diff = performance_data.get('avg_difficulty', 1)
    max_diff = performance_data.get('max_difficulty_reached', 1)
    
    # Difficulty level names
    diff_names = {1: 'Easy', 2: 'Medium', 3: 'Hard'}
    
    metrics_data = [
        ['Metric', 'Value'],
        ['Total Questions Attempted', str(total_q)],
        ['Correct Answers', f'{correct} ✓'],
        ['Incorrect Answers', f'{incorrect} ✗'],
        ['Accuracy Rate', f'{accuracy:.1f}%'],
        ['Average Difficulty', f'{avg_diff:.1f}/3 ({diff_names.get(round(avg_diff), "Medium")})'],
        ['Highest Difficulty Reached', f'{diff_names.get(max_diff, "Easy")}'],
    ]
    
    metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5282')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f7fafc')),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2d3748')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#e2e8f0')),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    
    story.append(metrics_table)
    story.append(Spacer(1, 20))
    
    # Performance Grade
    if accuracy >= 90:
        grade = "🌟 Excellent"
        grade_color = '#38a169'
    elif accuracy >= 75:
        grade = "👍 Good"
        grade_color = '#3182ce'
    elif accuracy >= 60:
        grade = "📈 Satisfactory"
        grade_color = '#d69e2e'
    else:
        grade = "📚 Needs Improvement"
        grade_color = '#e53e3e'
    
    grade_style = ParagraphStyle(
        'Grade',
        parent=styles['Heading2'],
        fontSize=14,
        alignment=1,
        textColor=colors.HexColor(grade_color),
        spaceBefore=10,
        spaceAfter=20
    )
    story.append(Paragraph(f"Overall Grade: {grade}", grade_style))
    
    # Topic Performance Section
    story.append(Paragraph("📝 Question-by-Question Analysis", heading_style))
    
    if questions_history:
        # Build question analysis table
        q_data = [['#', 'Topic', 'Difficulty', 'Result']]
        
        for i, q in enumerate(questions_history, 1):
            topic = q.get('topic', 'General')[:30]
            diff = diff_names.get(q.get('difficulty', 1), 'Medium')
            result = '✓ Correct' if q.get('is_correct', False) else '✗ Incorrect'
            q_data.append([str(i), topic, diff, result])
        
        q_table = Table(q_data, colWidths=[0.5*inch, 2.5*inch, 1*inch, 1*inch])
        q_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4a5568')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e0')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
        ]))
        
        story.append(q_table)
    else:
        story.append(Paragraph("No questions answered yet.", normal_style))
    
    story.append(Spacer(1, 20))
    
    # Weak Topics Section
    weak_topics = [q.get('topic', 'Unknown') for q in questions_history if not q.get('is_correct', False)]
    
    if weak_topics:
        story.append(Paragraph("⚠️ Topics Needing Review", heading_style))
        
        # Count topic occurrences
        topic_counts = {}
        for topic in weak_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        for topic, count in sorted(topic_counts.items(), key=lambda x: -x[1]):
            story.append(Paragraph(
                f"• <b>{topic}</b> - {count} incorrect answer(s)",
                normal_style
            ))
        
        story.append(Spacer(1, 15))
    
    # Improvement Suggestions Section
    story.append(Paragraph("💡 Personalized Recommendations", heading_style))
    
    # Process suggestions - split by lines and bullet points
    suggestions_lines = improvement_suggestions.strip().split('\n')
    for line in suggestions_lines:
        line = line.strip()
        if line:
            # Clean up markdown formatting
            line = line.replace('**', '').replace('*', '')
            line = line.replace('•', '').replace('-', '', 1).strip()
            if line:
                story.append(Paragraph(f"• {line}", normal_style))
    
    story.append(Spacer(1, 30))
    
    # Footer
    footer_style = ParagraphStyle(
        'Footer',
        parent=normal_style,
        alignment=1,
        textColor=colors.gray,
        fontSize=9
    )
    story.append(Paragraph("─" * 50, footer_style))
    story.append(Paragraph(
        "Generated by Quick Learn - Adaptive Assessment Platform",
        footer_style
    ))
    story.append(Paragraph(
        "Keep learning, keep growing! 🚀",
        footer_style
    ))
    
    # Build PDF
    doc.build(story)
    
    pdf_content = buffer.getvalue()
    buffer.close()
    
    return pdf_content


def get_weak_topics(questions_history: List[Dict]) -> List[str]:
    """
    Extract topics where the user performed poorly.
    
    Args:
        questions_history: List of question results
        
    Returns:
        List of weak topic names
    """
    weak_topics = []
    for q in questions_history:
        if not q.get('is_correct', False):
            topic = q.get('topic', 'Unknown')
            if topic not in weak_topics:
                weak_topics.append(topic)
    return weak_topics
