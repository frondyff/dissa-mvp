from datetime import datetime
from typing import List, Dict, Optional
from fpdf import FPDF

# Brand colours
BRAND_GREEN = (0, 120, 90)
BRAND_DARK = (30, 30, 30)
BRAND_LIGHT_GREY = (245, 245, 245)


def to_latin1(text: str) -> str:
    """
    Ensure text contains only Latin-1 characters (required by FPDF).
    Any unsupported characters are replaced with '?'.
    """
    if text is None:
        return ""
    return text.encode("latin-1", "replace").decode("latin-1")


def category_icon(category: str) -> str:
    """
    ASCII-safe 'icon' per category. If you later want true emoji,
    we need a Unicode font instead of Latin-1.
    """
    if not category:
        return "[SERVICE]"
    cat = category.lower()
    if "food" in cat:
        return "[FOOD]"
    if "health" in cat and "mental" not in cat:
        return "[HEALTH]"
    if "mental" in cat:
        return "[MENTAL]"
    if "housing" in cat or "shelter" in cat:
        return "[HOME]"
    if "clothes" in cat or "hygiene" in cat:
        return "[BASICS]"
    if "work" in cat or "employment" in cat:
        return "[WORK]"
    if "family" in cat or "children" in cat:
        return "[FAMILY]"
    if "culture" in cat or "community" in cat or "indigenous" in cat:
        return "[CULTURE]"
    return "[SERVICE]"


class HandoutPDF(FPDF):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.generated_on = ""

    # ----- Header -----
    def header(self):
        # Coloured banner
        self.set_fill_color(*BRAND_GREEN)
        self.rect(x=0, y=0, w=210, h=25, style="F")

        # Title
        self.set_xy(10, 7)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 18)
        self.cell(0, 8, to_latin1("Service Handout"), ln=1)

        # Date/time
        if self.generated_on:
            self.set_font("Helvetica", "", 10)
            self.set_x(10)
            self.cell(0, 6, to_latin1(f"Generated on: {self.generated_on}"), ln=1)

        self.ln(4)

    # ----- Footer -----
    def footer(self):
        self.set_y(-15)
        self.set_draw_color(220, 220, 220)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 200, self.get_y())

        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        footer_text = (
            f"NFCM / Centraide - DISSA MVP  |  Page {self.page_no()}/{{nb}}"
        )
        self.cell(0, 6, to_latin1(footer_text), align="C")


def generate_pdf(
    handout_text: str,
    visitor_context: Dict,
    services: Optional[List[Dict]] = None,
) -> bytes:
    """
    Generate a styled PDF.
    If `services` is provided, we render one 'card' per service.
    """

    pdf = HandoutPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.alias_nb_pages()
    pdf.generated_on = datetime.now().strftime("%Y-%m-%d %H:%M")

    pdf.add_page()
    pdf.set_text_color(*BRAND_DARK)
    pdf.set_font("Helvetica", size=12)

    left_margin = 15
    right_margin = 15
    usable_width = 210 - left_margin - right_margin

    # ----- Intro text (first paragraph of LLM handout) -----
    intro = ""
    closing = ""
    if handout_text:
        parts = handout_text.strip().split("\n\n")
        if parts:
            intro = parts[0]
        if len(parts) > 1:
            closing = parts[-1]

    if intro:
        pdf.set_xy(left_margin, pdf.get_y())
        pdf.multi_cell(usable_width, 6, to_latin1(intro))
        pdf.ln(4)

    # ----- Service cards -----
    if services:
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 8, to_latin1("Services that may help you:"), ln=1)
        pdf.ln(2)
        pdf.set_font("Helvetica", size=11)

        for svc in services:
            name = svc.get("name", "Service")
            desc = svc.get("description", "")
            address = svc.get("address", "")
            hours = svc.get("hours_today", "")
            category = svc.get("category", "")

            icon = category_icon(category)

            # Card background
            pdf.set_fill_color(*BRAND_LIGHT_GREY)
            pdf.set_draw_color(210, 210, 210)
            pdf.set_line_width(0.4)

            pdf.set_x(left_margin)
            # Title row (bordered)
            title_line = f"{icon}  {name}"
            pdf.multi_cell(
                usable_width,
                7,
                to_latin1(title_line),
                border=1,
                fill=True,
            )

            # Body row (description, hours, address)
            pdf.set_x(left_margin)
            body_lines = []

            if desc:
                body_lines.append(desc)
            if hours:
                body_lines.append(f"Today: {hours}")
            if address:
                body_lines.append(f"Where: {address}")

            body_text = "\n".join(body_lines)
            if body_text:
                pdf.multi_cell(
                    usable_width,
                    6,
                    to_latin1(body_text),
                    border=1,
                    fill=False,
                )

            pdf.ln(3)  # space between cards
    else:
        # Fallback: original behaviour — whole text as one block
        pdf.set_xy(left_margin, pdf.get_y())
        pdf.multi_cell(usable_width, 7, to_latin1(handout_text or ""))

    # ----- Closing line from LLM, if available -----
    if closing:
        pdf.ln(4)
        pdf.set_font("Helvetica", size=11)
        pdf.multi_cell(usable_width, 6, to_latin1(closing))

    pdf_bytes = pdf.output(dest="S").encode("latin-1")
    return pdf_bytes
