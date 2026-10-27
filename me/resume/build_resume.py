from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "George_Abrahamyants_Resume_Oct2026.pdf"

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
pdfmetrics.registerFont(TTFont("DejaVu", str(FONT_DIR / "DejaVuSans.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(FONT_DIR / "DejaVuSans-Bold.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-Oblique", str(FONT_DIR / "DejaVuSans-Oblique.ttf")))
pdfmetrics.registerFont(TTFont("DejaVu-BoldOblique", str(FONT_DIR / "DejaVuSans-BoldOblique.ttf")))
pdfmetrics.registerFontFamily("DejaVu", normal="DejaVu", bold="DejaVu-Bold", italic="DejaVu-Oblique", boldItalic="DejaVu-BoldOblique")

INK = colors.HexColor("#17202A")
ACCENT = colors.HexColor("#1F5A7A")
MUTED = colors.HexColor("#4C5963")
RULE = colors.HexColor("#A9BAC4")


def p(text, style, bullet=None):
    return Paragraph(text, style, bulletText=bullet)


styles = getSampleStyleSheet()
name = ParagraphStyle(
    "Name",
    fontName="DejaVu-Bold",
    fontSize=18,
    leading=21,
    alignment=TA_CENTER,
    textColor=INK,
    spaceAfter=2,
)
contact = ParagraphStyle(
    "Contact",
    fontName="DejaVu",
    fontSize=7.9,
    leading=9.8,
    alignment=TA_CENTER,
    textColor=MUTED,
    spaceAfter=2,
)
tagline = ParagraphStyle(
    "Tagline",
    fontName="DejaVu-Bold",
    fontSize=8.4,
    leading=10,
    alignment=TA_CENTER,
    textColor=ACCENT,
    spaceAfter=4,
)
section = ParagraphStyle(
    "Section",
    fontName="DejaVu-Bold",
    fontSize=10,
    leading=11.6,
    textColor=ACCENT,
    spaceBefore=5.2,
    spaceAfter=2,
    keepWithNext=True,
)
role = ParagraphStyle(
    "Role",
    fontName="DejaVu-Bold",
    fontSize=8.95,
    leading=10.8,
    textColor=INK,
    spaceBefore=3.8,
    spaceAfter=1.2,
    keepWithNext=True,
)
body = ParagraphStyle(
    "Body",
    fontName="DejaVu",
    fontSize=8.65,
    leading=10.55,
    textColor=INK,
    spaceAfter=1.7,
)
bullet = ParagraphStyle(
    "Bullet",
    parent=body,
    leftIndent=12,
    firstLineIndent=-8,
    bulletIndent=1,
    spaceAfter=2.15,
)
compact = ParagraphStyle(
    "Compact",
    parent=body,
    fontSize=8.45,
    leading=10.15,
    spaceAfter=1.4,
)


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.35)
    canvas.line(doc.leftMargin, 0.42 * inch, LETTER[0] - doc.rightMargin, 0.42 * inch)
    canvas.setFont("DejaVu", 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(doc.leftMargin, 0.28 * inch, "George Abrahamyants")
    canvas.drawRightString(
        LETTER[0] - doc.rightMargin,
        0.28 * inch,
        f"Page {doc.page}",
    )
    canvas.restoreState()


doc = SimpleDocTemplate(
    str(OUTPUT),
    pagesize=LETTER,
    leftMargin=0.46 * inch,
    rightMargin=0.46 * inch,
    topMargin=0.38 * inch,
    bottomMargin=0.5 * inch,
    title="George Abrahamyants - Resume",
    author="George Abrahamyants",
    subject="AI products and operations, AI evaluation and governance, legal and regulated operations",
)


def b(text):
    return p(text, bullet, "•")


story = [
    p("GEORGE ABRAHAMYANTS", name),
    p(
        "Daly City, CA 94015  |  415-632-8008  |  "
        '<link href="mailto:gugosf@berkeley.edu" color="#4C5963">gugosf@berkeley.edu</link>  |  '
        '<link href="https://www.linkedin.com/in/george-abrahamyan" color="#4C5963">linkedin.com/in/george-abrahamyan</link>  |  '
        '<link href="https://github.com/gugosf114" color="#4C5963">github.com/gugosf114</link>  |  '
        '<link href="https://abrahamyants.github.io" color="#4C5963">abrahamyants.github.io</link>',
        contact,
    ),
    p("AI PRODUCTS &amp; OPERATIONS  |  AI EVALUATION  |  AI GOVERNANCE  |  JD", tagline),
    HRFlowable(width="100%", thickness=0.7, color=ACCENT, spaceAfter=2),
    p("SUMMARY", section),
    p(
        "JD who builds AI products and runs them in real use: WiM and Lavrentiy, voice-to-intent apps for Android and Windows with a 35-claim patent application, Bakers Agent, a Google Cloud system running a live business's marketing behind human approval gates, and NoiseFile, a published Android app on Google Play. Earlier: multistate tax controversy at Andersen, a federal benefits decision affirmed on appeal, and a $1.75 million regulated buildout.",
        body,
    ),
    p("AI DEVELOPER &amp; INDEPENDENT RESEARCHER | Self-Employed | June 2025-Present", section),
    b("<b>WiM and Lavrentiy:</b> Built voice-to-intent apps for Android and Windows: the user speaks, and clean text lands in the app in use. A speech-disfluency layer lets the user end the recording, detects blocks and covert word substitutions, and asks at most three clarifying questions. WiM is in Google Play closed testing; Lavrentiy v1.7.11 installs on Windows and works offline."),
    b("<b>Patent:</b> Sole inventor on a 35-claim U.S. provisional patent application covering the combined mobile and desktop architecture (App. No. 64/100,336; filed June 27, 2026)."),
    b("<b>Bakers Agent:</b> Built and operate a Google Cloud system (40+ Cloud Functions, React/TypeScript dashboard) that runs a live business's marketing behind human approval gates: photos become approved posts on Google Business Profile, Facebook, and Pinterest; Search Console findings become GitHub pull requests with a quality gate and feedback loop; photo batches become priced Google menus; review replies are drafted for approval; one dashboard tracks traffic, search, reviews, AI-search visibility, social reach, and payments. Shared backend for WiM and Lavrentiy; a multi-client version, Bakers Agent 2, is in progress."),
    b("<b>Agent Bridge:</b> Built an agent that operates the owner's own phone and laptop: it reads notifications, drives apps on hidden screens, reads SMS sign-in codes, and pauses for approval before any irreversible step. A companion web agent booked and cancelled a live restaurant reservation."),
    b("<b>Legal and compliance tools:</b> Published NoiseFile on Google Play, a local-first Android app that turns the noise codes of 36 Bay Area cities into 108 complaint workflows, and Audit Ledger, a tamper-evident California residency audit-defense system (19 <i>Bragg</i> factors, SHA-256 hash chain, contradiction checks)."),
    b("<b>Client and business sites:</b> Built and operate mybakingcreations.com (44 pages, PayPal checkout, chatbot). Delivered a paid website and field-operations app for a private-jet detailing company, with photo inspections, damage markup, manager-only quality sign-off, and shareable customer reports."),
    p("LEGAL, TAX &amp; REGULATED OPERATIONS", section),
    p("Andersen - Senior Associate, State &amp; Local Tax | San Francisco | November 2023-April 2025", role),
    b("Managed multistate tax compliance and controversy for corporate and startup clients, including audit defense, refund claims, voluntary disclosures, and nexus reviews; led engagements disputing the state tax treatment of major technology transactions and negotiated audit resolutions that reduced client liabilities."),
    b("Used LLM tools to analyze public-company SEC filings for active audits, litigation, and credits-and-incentives positions; drafted memoranda and recommendations across income/franchise and sales-and-use tax."),
    p("Phenotopia - Chief Operations Officer | Santa Rosa | February 2021-May 2023", role),
    b("Directed a $1.75 million retail buildout through permits, construction, final municipal inspections, and opening; managed contractors, engineers, consultants, municipal departments, vendor contracts, MSAs, NDAs, purchasing, and SOPs. The business remains open."),
    b("Separately authored the 33-page conditional-use-permit application for a 9,990 sq. ft. cultivation, distribution, and non-volatile manufacturing facility and assembled its 11 exhibits from five outside firms (civil engineering, traffic, HVAC odor control, security, water treatment), about $300,000 of work, through 16 months of drafts and city review; the project won unanimous local approval and state licensing."),
    p("Andersen - Associate, State &amp; Local Tax | August 2018-January 2021", role),
    b("Conducted nexus studies, multistate compliance reviews, and exposure analyses across 20+ jurisdictions; supported audits, voluntary disclosures, refund claims, and controversy matters (intern from February 2018)."),
    p("EARLIER LEGAL EXPERIENCE", section),
    p(
        "<b>U.S. Department of Labor, OALJ</b> - Judicial Extern to ALJ Richard M. Clark (2017): drafted the 23-page Decision and Order in a Defense Base Act psychological-injury claim, weighing conflicting expert opinions and symptom-validity testing; affirmed by the Benefits Review Board, <i>Baba v. SOS International, LLC</i>, BRB No. 17-0440 (Jan. 30, 2018).<br/>"
        "<b>IRS Office of Chief Counsel</b> - Legal Extern (2017)  |  <b>USPS Pacific Area Law Office</b> - Legal Extern (2017)",
        compact,
    ),
    p("EDUCATION", section),
    p(
        "<b>UC College of the Law, San Francisco (UC Hastings)</b> - JD, Tax Concentration, 2018 | CALI Award | Production Editor, <i>Hastings Business Law Journal</i><br/>"
        "<b>University of California, Berkeley</b> - BA, Political Science; Minor, Southeast Asian Studies, 2015 | 3.85 | Distinction in General Scholarship<br/>"
        "<b>Languages:</b> English | Armenian (native) | Russian (fluent)",
        compact,
    ),
]

doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
print(OUTPUT)
