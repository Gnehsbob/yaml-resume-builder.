import yaml
import sys
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, ListFlowable, ListItem
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

# ============ COLOR SCHEME ============
COLORS = {
    'primary': HexColor('#5EEAD4'),      # Teal accent
    'background': HexColor('#1E293B'),   # Dark slate
    'text': HexColor('#E2E8F0'),         # Light gray (used for lines)
    'muted': HexColor('#94A3B8'),        # Muted gray
    'card': HexColor('#334155'),         # Card background
}

# ============Background Painter ==============

def draw_background(canvas, doc):
    """Draws the dark background on every page."""
    canvas.saveState()
    canvas.setFillColor(COLORS['background'])
    canvas.rect(0, 0, A4[0], A4[1], fill=1)
    canvas.restoreState()

# ============ CUSTOM STYLES ============
def create_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name='CVName',
        parent=styles['Heading1'],
        fontSize=28,
        textColor=COLORS['text'],
        spaceAfter=4*mm,
        fontName='Helvetica-Bold',
        leading=32,
    ))

    styles.add(ParagraphStyle(
        name='CVTitle',
        parent=styles['Normal'],
        fontSize=14,
        textColor=COLORS['primary'],
        spaceAfter=6*mm,
        fontName='Helvetica',
    ))

    styles.add(ParagraphStyle(
        name='SectionHeading',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=COLORS['primary'],
        spaceBefore=8*mm,
        spaceAfter=4*mm,
        fontName='Helvetica-Bold',
    ))

    styles.add(ParagraphStyle(
        name='CVBody',
        parent=styles['Normal'],
        fontSize=10,
        textColor=COLORS['text'],
        alignment=TA_JUSTIFY,
        leading=14,
        spaceAfter=2*mm,
    ))

    styles.add(ParagraphStyle(
        name='Contact',
        parent=styles['Normal'],
        fontSize=9,
        textColor=COLORS['muted'],
        spaceAfter=1*mm,
    ))

    return styles

# ============ DATA LOADER ============

def load_cv_data(filepath):
    """Loads data and handles errors like a SysAdmin tool."""
    if not os.path.exists(filepath):
        print(f"ERROR: File '{filepath}' not found.")
        sys.exit(1)

    with open(filepath, 'r') as file:
        return yaml.safe_load(file)

# --- Command Line Arguments ---
if len(sys.argv) > 1:
    data_file = sys.argv[1]      # Path provided via shell
else:
    data_file = 'cv_data.yaml'   # Default filename

# Load the data
cv_data = load_cv_data(data_file)

# ============ PDF GENERATION ============

def build_cv(output_filename='my_cv.pdf'):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    styles = create_styles()
    story = []

    # --- Header ---
    story.append(Paragraph(cv_data['name'], styles['CVName']))
    story.append(Paragraph(cv_data['title'], styles['CVTitle']))

    contact = cv_data['contact']
    # Contact line with hardcoded GitHub and LinkedIn URLs
    contact_text = (
        f"{contact['phone']} | {contact['email']} | {contact['location']}<br/>"
        f'<a href="https://github.com/Gnehsbob/Gnehsbob.git">GitHub</a> | '
        f'<a href="https://www.linkedin.com/in/bokgosi-letebele-537b7a207?lipi=urn%3Ali%3Apage%3Ad_flagship3_profile_view_base_contact_details%3BfeAwj0okRNmpnV43K8cp3w%3D%3D">LinkedIn</a>'
    )
    story.append(Paragraph(contact_text, styles['Contact']))
    story.append(Spacer(1, 6*mm))

    # --- Horizontal line separator (white) after contact info ---
    story.append(Spacer(1, 2*mm))
    line_table = Table([['']], colWidths=[doc.width], rowHeights=1)
    line_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), COLORS['text']),  # Light gray line
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(line_table)
    story.append(Spacer(1, 2*mm))

    # --- Profile Section (two columns for focus & goal) ---
    story.append(Paragraph('PROFILE', styles['SectionHeading']))

    profile = cv_data['profile']
    profile_story = []

    if isinstance(profile, dict):
        # Summary (full width)
        if 'summary' in profile:
            profile_story.append(Paragraph(profile['summary'], styles['CVBody']))
            profile_story.append(Spacer(1, 2*mm))

        # Build left column for Focus Areas
        left_col = []
        if 'focus' in profile and profile['focus']:
            left_col.append(Paragraph("<b>Focus Areas:</b>", styles['CVBody']))
            for item in profile['focus']:
                left_col.append(Paragraph(f"• {item}", styles['CVBody']))
            left_col.append(Spacer(1, 1*mm))

        # Build right column for Current Goal
        right_col = []
        if 'current_goal' in profile and profile['current_goal']:
            right_col.append(Paragraph("<b>Current Goal:</b>", styles['CVBody']))
            right_col.append(Paragraph(profile['current_goal'], styles['CVBody']))
            right_col.append(Spacer(1, 1*mm))

        # Only create the two-column table if at least one column has content
        if left_col or right_col:
            data = [[
                left_col if left_col else [Spacer(1, 1*mm)],
                right_col if right_col else [Spacer(1, 1*mm)]
            ]]
            col_width = (doc.width - 10) / 2.0
            profile_table = Table(data, colWidths=[col_width, col_width])
            profile_table.setStyle(TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('LEFTPADDING', (0,0), (-1,-1), 5),
                ('RIGHTPADDING', (0,0), (-1,-1), 5),
                ('TOPPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
                ('BACKGROUND', (0,0), (-1,-1), COLORS['background']),
                ('LINE AFTER', (0,0), (0,-1), 1, COLORS['primary']),  # teal line for profile
            ]))
            profile_story.append(profile_table)
        else:
            # Fallback if no focus/goal: just the profile text (already added)
            pass

        story.extend(profile_story)
    else:
        story.append(Paragraph(profile, styles['CVBody']))

    # --- Skills & Education side-by-side ---
    skills_col = []
    skills_col.append(Paragraph('KEY SKILLS', styles['SectionHeading']))
    for entry in cv_data['skills']:
        category = entry['category']
        items = ", ".join(entry['items'])
        skills_col.append(Paragraph(f"<b>{category}:</b> {items}", styles['CVBody']))
    skills_col.append(Spacer(1, 3*mm))

    edu_col = []
    edu_col.append(Paragraph('EDUCATION', styles['SectionHeading']))
    for edu in cv_data['education']:
        edu_text = f"<b>{edu['degree']}</b><br/>{edu['institution']} — {edu['graduation']}"
        edu_col.append(Paragraph(edu_text, styles['CVBody']))
        if 'notes' in edu:
            for note in edu['notes']:
                edu_col.append(Paragraph(f"• {note}", styles['CVBody']))
        edu_col.append(Spacer(1, 2*mm))
    edu_col.append(Spacer(1, 3*mm))

    col_width = (doc.width - 10) / 2.0
    data_skilledu = [[skills_col, edu_col]]
    table_skilledu = Table(data_skilledu, colWidths=[col_width, col_width])
    table_skilledu.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('BACKGROUND', (0,0), (-1,-1), COLORS['background']),
        # White vertical line between columns, starting after first column, spanning all rows
        ('LINE AFTER', (0,0), (0,-1), 1, COLORS['text']),
    ]))
    story.append(table_skilledu)

    # --- Experience/Projects (full width) ---
    story.append(Paragraph('PROJECTS & EXPERIENCE', styles['SectionHeading']))
    for exp in cv_data['experience']:
        story.append(Paragraph(f"<b>{exp['title']}</b> — {exp['period']}", styles['CVBody']))
        for bullet in exp['bullets']:
            story.append(Paragraph(f"• {bullet}", styles['CVBody']))
        story.append(Spacer(1, 3*mm))

    # --- Certifications (full width) ---
    if 'certifications' in cv_data:
        story.append(Paragraph('CERTIFICATIONS', styles['SectionHeading']))
        for cert in cv_data['certifications']:
            if isinstance(cert, list):
                story.append(Paragraph(f"<b>{cert[0]}</b> — {cert[1]}", styles['CVBody']))
            else:
                story.append(Paragraph(f"• {cert}", styles['CVBody']))

    # Build the PDF with background
    doc.build(
        story,
        onFirstPage=draw_background,
        onLaterPages=draw_background
    )
    print(f" PDF successfully generated: {output_filename}")

if __name__ == '__main__':
    build_cv('professional_cv.pdf')