"""
Invoice PDF (FR9). Data is read from the DATABASE (single source of truth),
then drawn with ReportLab.
"""
from datetime import datetime
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.db import get_conn

INVOICES_DIR = Path(__file__).resolve().parent.parent / "invoices"

BRAND = colors.HexColor("#0F766E")      # teal
LIGHT = colors.HexColor("#F0FDFA")      # very light teal
GREY = colors.HexColor("#6B7280")
LINE = colors.HexColor("#D1D5DB")

INVOICE_SQL = """
    SELECT i.invoice_no, i.amount, i.issued_at, i.pdf_file,
           a.appointment_id, a.reason,
           p.full_name AS patient_name, p.phone AS patient_phone,
           d.full_name AS doctor_name, d.speciality, d.room, d.floor,
           s.slot_date, s.start_time
    FROM invoices i
    JOIN appointments a ON a.appointment_id = i.appointment_id
    JOIN patients p     ON p.patient_id = a.patient_id
    JOIN doctors d      ON d.doctor_id = a.doctor_id
    JOIN slots s        ON s.slot_id = a.slot_id
    WHERE i.invoice_no = ?
"""


def _money(value: float) -> str:
    return f"LKR {value:,.2f}"


def _load_invoice_data(invoice_no: str) -> tuple[dict, dict]:
    with get_conn() as conn:
        inv = conn.execute(INVOICE_SQL, (invoice_no,)).fetchone()
        hosp = conn.execute("SELECT * FROM hospital_info WHERE id = 1").fetchone()
    if inv is None or hosp is None:
        raise ValueError(f"Invoice {invoice_no} not found")
    return dict(inv), dict(hosp)


def build_invoice_pdf(invoice_no: str) -> Path:
    """Create the PDF for an invoice that already exists in the database."""
    inv, hosp = _load_invoice_data(invoice_no)
    INVOICES_DIR.mkdir(parents=True, exist_ok=True)
    path = INVOICES_DIR / inv["pdf_file"]
    _render_pdf(inv, hosp, path)
    return path


def _render_pdf(inv: dict, hosp: dict, path: Path) -> None:
    styles = getSampleStyleSheet()
    title = ParagraphStyle("t", parent=styles["Title"], textColor=BRAND,
                           alignment=0, fontSize=20, leading=24, spaceAfter=4)
    small = ParagraphStyle("s", parent=styles["Normal"], fontSize=9, leading=12, textColor=GREY)
    body = ParagraphStyle("b", parent=styles["Normal"], fontSize=10, leading=13)
    heading = ParagraphStyle("h", parent=styles["Heading3"], textColor=BRAND,
                             spaceBefore=8, spaceAfter=4)
    e = lambda v: escape(str(v or "-"))      # escape & < > - needed ONLY inside Paragraph(...)

    # ---- 1. Header: hospital (left) + invoice box (right) ----
    hospital_block = [
        Paragraph(e(hosp["name"]), title),
        Paragraph(f"{e(hosp['address'])}<br/>Tel: {e(hosp['phone'])} | Email: {e(hosp['email'])}"
                  f"<br/>Emergency: {e(hosp['emergency_number'])}", small),
    ]
    invoice_box = Table([
        ["INVOICE", ""],
        ["Invoice No", inv["invoice_no"]],
        ["Date", inv["issued_at"][:10]],
        ["Appointment", f"APT-{inv['appointment_id']:04d}"],
    ], colWidths=[26 * mm, 34 * mm])
    invoice_box.setStyle(TableStyle([
        ("SPAN", (0, 0), (1, 0)),
        ("BACKGROUND", (0, 0), (1, 0), BRAND),
        ("TEXTCOLOR", (0, 0), (1, 0), colors.white),
        ("FONTNAME", (0, 0), (1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (1, 0), 12),
        ("ALIGN", (0, 0), (1, 0), "CENTER"),
        ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("BOX", (0, 0), (-1, -1), 0.8, BRAND),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    header = Table([[hospital_block, invoice_box]], colWidths=[114 * mm, 60 * mm])
    header.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"),
                                ("LEFTPADDING", (0, 0), (-1, -1), 0)]))

    # ---- 2. Patient + appointment details ----
    visit_date = datetime.fromisoformat(inv["slot_date"]).strftime("%A, %d %B %Y")
    details = Table([
        ["Patient", inv["patient_name"], "Doctor", inv["doctor_name"]],
        ["Phone", inv["patient_phone"], "Speciality", inv["speciality"]],
        ["Visit date", visit_date, "Time", inv["start_time"]],
        ["Reason", Paragraph(e(inv["reason"]), body), "Room", f"{inv['room']}, {inv['floor']}"],
    ], colWidths=[24 * mm, 63 * mm, 24 * mm, 63 * mm])
    details.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT),
        ("BACKGROUND", (2, 0), (2, -1), LIGHT),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 0.5, LINE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))

    # ---- 3. Charges ----
    charges = Table([
        ["Description", "Amount"],
        [f"Consultation - {inv['speciality']} ({inv['doctor_name']})", _money(inv["amount"])],
        ["Total", _money(inv["amount"])],
    ], colWidths=[124 * mm, 50 * mm])
    charges.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRAND),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, -1), (-1, -1), 11),
        ("LINEABOVE", (0, -1), (-1, -1), 1, BRAND),
        ("LINEBELOW", (0, 1), (-1, 1), 0.5, LINE),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))

    # ---- 4. Useful information + footer ----
    story = [
        header, Spacer(1, 8 * mm),
        Paragraph("Appointment details", heading), details, Spacer(1, 6 * mm),
        Paragraph("Charges", heading), charges, Spacer(1, 6 * mm),
        Paragraph("<b>Payment status:</b> Pay at the counter on the day of the visit.", body),
        Paragraph(f"<b>Accepted payment methods:</b> {e(hosp['payment_methods'])}", body),
        Paragraph(f"<b>Please bring:</b> {e(hosp['what_to_bring'])}", body),
        Spacer(1, 10 * mm),
        Paragraph("This is a computer-generated invoice from Celia, the front desk assistant. "
                  "Demo project - dummy data only.", small),
    ]
    doc = SimpleDocTemplate(str(path), pagesize=A4, title=f"Invoice {inv['invoice_no']}",
                            leftMargin=18 * mm, rightMargin=18 * mm,
                            topMargin=18 * mm, bottomMargin=18 * mm)
    doc.build(story)