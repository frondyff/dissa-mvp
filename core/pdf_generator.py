from fpdf import FPDF
from datetime import datetime

def generate_pdf(handout_text: str, visitor_context: dict) -> bytes:
    """
    Generates a PDF file (as bytes) from the handout text.
    Visitor metadata (age, language, needs) is NOT included for privacy.
    """

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Service Handout", ln=True)
    pdf.ln(5)

    # Timestamp only (allowed)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 6, f"Generated on: {now_str}")
    pdf.ln(5)

    # Main handout content
    pdf.set_font("Arial", size=12)
    for line in handout_text.split("\n"):
        pdf.multi_cell(0, 8, line)

    # Export PDF as bytes
    return pdf.output(dest="S").encode("latin1")
