from datetime import datetime
from typing import List, Dict, Optional
from fpdf import FPDF

# Brand colours
BRAND_GREEN = (0, 120, 90)
BRAND_DARK = (30, 30, 30)
BRAND_LIGHT_GREY = (245, 245, 245)


def to_latin1(text: str) -> str:
    if text is None:
        return ""
    return text.encode("latin-1", "replace").decode("latin-1")


def category_icon(category: str) -> str:
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
        # Green banner
        self.set_fill_color(*BRAND_GREEN)
        self.rect(x=0, y=0, w=210, h=25, style="F")

        # Title
        self.set_xy(15, 7)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 18)
        self.cell(0, 8, to_latin1("Service Handout"))

        # Date/time
        if self.generated_on:
            self.set_y(17)
            self.set_font("Helvetica", "", 10)
            self.set_x(15)
            self.cell(0, 6, to_latin1(f"Generated on: {self.generated_on}"))

        self.ln(10)

    # ----- Footer -----
    def footer(self):
        self.set_y(-15)
        self.set_draw_color(220, 220, 220)
        self.set_line_width(0.3)
        self.line(15, self.get_y(), 195, self.get_y())

        self.set_y(-12)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(120, 120, 120)
        footer_text = (
            f"NFCM / Centraide - DISSA MVP  |  Page {self.page_no()}/{{nb}}"
        )
        self.cell(0, 6, to_latin1(footer_text), align="C")


def draw_service_card(pdf: HandoutPDF, left_margin: int, usable_width: int, svc: Dict):
    """
    Draw one service card with:
    [CATEGORY] Name
    Description
    Today: ...
    Where: ...
    """
    name = svc.get("name", "Service")
    desc = svc.get("description", "")
    address = svc.get("address", "")
    hours = svc.get("hours_today", "")
    category = svc.get("category", "")

    icon = category_icon(category)

    start_x = left_margin
    start_y = pdf.get_y()

    inner_padding_x = 3
    inner_padding_y = 3

    # --- First pass: place text to measure height ---
    pdf.set_xy(start_x + inner_padding_x, start_y + inner_padding_y)
    pdf.set_font("Helvetica", "B", 11)
    title_line = f"{icon}  {name}"
    text_width = usable_width - 2 * inner_padding_x
    pdf.multi_cell(text_width, 6, to_latin1(title_line))

    pdf.set_font("Helvetica", size=10)
    body_lines = []
    if desc:
        body_lines.append(desc)
    if hours:
        body_lines.append(f"Today: {hours}")
    if address:
        body_lines.append(f"Where: {address}")
    body_text = "\n".join(body_lines)

    if body_text:
        pdf.ln(1)
        pdf.multi_cell(text_width, 5, to_latin1(body_text))

    end_y = pdf.get_y()
    card_height = end_y - start_y + inner_padding_y

    # --- Draw card border/background ---
    pdf.set_draw_color(210, 210, 210)
    pdf.set_fill_color(255, 255, 255)
    pdf.set_line_width(0.4)
    pdf.rect(start_x, start_y, usable_width, card_height, style="D")

    # --- Second pass: redraw text on top of the card ---
    pdf.set_xy(start_x + inner_padding_x, start_y + inner_padding_y)
    pdf.set_font("Helvetica", "B", 11)
    pdf.multi_cell(text_width, 6, to_latin1(title_line))

    pdf.set_font("Helvetica", size=10)
    if body_text:
        pdf.ln(1)
        pdf.multi_cell(text_width, 5, to_latin1(body_text))

    # Space before next card
    pdf.ln(4)


def generate_pdf(
    handout_text: str,
    visitor_context: Dict,
    services: Optional[List[Dict]] = None,
) -> bytes:
    """
    Generate a styled PDF.
    If `services` is provided, render one clean card per service.
    """
    pdf = HandoutPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.alias_nb_pages()
    pdf.generated_on = datetime.now().strftime("%Y-%m-%d %H:%M")

    pdf.add_page()
    pdf.set_text_color(*BRAND_DARK)

    left_margin = 15
    right_margin = 15
    usable_width = 210 - left_margin - right_margin

    # Split LLM text into intro + closing
    intro = ""
    closing = ""
    if handout_text:
        parts = handout_text.strip().split("\n\n")
        if parts:
            intro = parts[0]
        if len(parts) > 1:
            closing = parts[-1]

    # Intro sentence
    if intro:
        pdf.set_font("Helvetica", size=11)
        pdf.set_xy(left_margin, pdf.get_y())
        pdf.multi_cell(usable_width, 5.5, to_latin1(intro))
        pdf.ln(5)

    # Section title + cards
    if services:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_x(left_margin)
        pdf.cell(0, 7, to_latin1("Services that may help you:"), ln=1)
        pdf.ln(2)

        for svc in services:
            # Avoid cutting a card at bottom of page
            if pdf.get_y() > 260:
                pdf.add_page()
            draw_service_card(pdf, left_margin, usable_width, svc)
    else:
        # Fallback: just show full text if no structured services
        pdf.set_font("Helvetica", size=11)
        pdf.set_xy(left_margin, pdf.get_y())
        pdf.multi_cell(usable_width, 5.5, to_latin1(handout_text or ""))

    # Closing line
    if closing:
        pdf.ln(4)
        pdf.set_font("Helvetica", size=10)
        pdf.multi_cell(usable_width, 5, to_latin1(closing))

    pdf_bytes = pdf.output(dest="S")
    if isinstance(pdf_bytes, bytearray):
        pdf_bytes = bytes(pdf_bytes)
    return pdf_bytes
