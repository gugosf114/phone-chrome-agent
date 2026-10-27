#!/usr/bin/env python3
"""make_letter.py apply/<jobId>  — builds apply/<jobId>/cover-letter.pdf from cover-letter.txt + meta.json with the SAME header
as the resume (me/resume/build_resume.py): DejaVu Sans, centered name, muted contact line with GitHub, navy rule.
George 10/27: the letter must look like page two of the resume."""
import sys, os, json, datetime
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer
from xml.sax.saxutils import escape
D = sys.argv[1].rstrip('/'); meta = json.load(open(os.path.join(D, 'meta.json'))); text = open(os.path.join(D, 'cover-letter.txt')).read().strip()
F = "/usr/share/fonts/truetype/dejavu"
pdfmetrics.registerFont(TTFont("DejaVu", f"{F}/DejaVuSans.ttf")); pdfmetrics.registerFont(TTFont("DejaVu-Bold", f"{F}/DejaVuSans-Bold.ttf"))
INK, ACCENT, MUTED = colors.HexColor("#17202A"), colors.HexColor("#1F5A7A"), colors.HexColor("#4C5963")
name = ParagraphStyle("n", fontName="DejaVu-Bold", fontSize=18, leading=21, alignment=TA_CENTER, textColor=INK, spaceAfter=2)
contact = ParagraphStyle("c", fontName="DejaVu", fontSize=7.9, leading=9.8, alignment=TA_CENTER, textColor=MUTED, spaceAfter=6)
body = ParagraphStyle("b", fontName="DejaVu", fontSize=10, leading=14, textColor=INK, spaceAfter=9)
small = ParagraphStyle("s", parent=body, textColor=MUTED, spaceAfter=2)
out = os.path.join(D, 'cover-letter.pdf')
doc = SimpleDocTemplate(out, pagesize=LETTER, leftMargin=0.8*inch, rightMargin=0.8*inch, topMargin=0.6*inch, bottomMargin=0.6*inch, title=f"George Abrahamyants — Cover Letter — {meta['company']}", author="George Abrahamyants")
story = [Paragraph("GEORGE ABRAHAMYANTS", name),
  Paragraph('Daly City, CA 94015  |  415-632-8008  |  <link href="mailto:gugosf@berkeley.edu" color="#4C5963">gugosf@berkeley.edu</link>  |  <link href="https://www.linkedin.com/in/george-abrahamyan" color="#4C5963">linkedin.com/in/george-abrahamyan</link>  |  <link href="https://github.com/gugosf114" color="#4C5963">github.com/gugosf114</link>', contact),
  HRFlowable(width="100%", thickness=0.7, color=ACCENT, spaceAfter=14),
  Paragraph(datetime.date.today().strftime("%B %d, %Y").replace(" 0", " "), small),
  Paragraph(f"{escape(meta['company'])}<br/>Re: {escape(meta['title'])}", body), Spacer(1, 4)]
for para in text.split("\n\n"): story.append(Paragraph(escape(para).replace("\n", "<br/>"), body))
doc.build(story); print(out)
