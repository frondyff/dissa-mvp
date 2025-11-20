from datetime import datetime
from fpdf import FPDF


# Simple brand colours (you can tweak these)
BRAND_GREEN = (0, 120, 90)      # header bar
BRAND_DARK = (30, 30, 30)       # main text
BRAND_LIGHT_GREY = (245, 245, 245)


class HandoutPDF(FPDF):
    """
    Custom PDF with a coloured header and footer for the DISSA handout.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # this gets filled in by generate_pdf
        self.generated_on = ""

    # ----- Header -----
    def header(self):
        # Full-width coloured banner at the top
        self.set_fill_color(*BRAND_GREEN)
        self.rect(x=0, y=0, w=210, h=25, style="F")  # A4 width ~210mm

        # Title text
        self.set_xy(10, 7)
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 18)
        self.cell(0, 8, "Service Handout", ln=1)

        # Generated-on line (still in white, but smaller)
        if self.generated_on:
            self.set_font("Helvetica", "", 10)
            self.set_x(10)
            self.cell(0, 6, f"Generated on: {self.generated_on}", ln=1)

        # Move cursor a bit below the header area
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
        footer_text = f"NFCM / Centraide – DISSA MVP   •   Page {self.page_no()}/{{nb}}"
        self.cell(0, 6, footer_text, align="C")


def generate_pdf(handout_text: str, visitor_context: dict) -> bytes:
    """
    Generates a styled PDF file (as bytes) from the handout text.

    NOTE: We intentionally do NOT print age group, language, etc. here
    to keep the handout focused on services and avoid showing internal
    visitor context to the client.
    """

    pdf = HandoutPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.alias_nb_pages()

    # Timestamp for header
    pdf.generated_on = datetime.now().strftime("%Y-%m-%d %H:%M")

    # New page with our custom header
    pdf.add_page()

    # Body styling
    pdf.set_text_color(*BRAND_DARK)
    pdf.set_font("Helvetica", size=12)

    # Add a light background behind the main content block
    # (gives a "card" feeling similar to a web panel)
    left_margin = 15
    right_margin = 15
    usable_width = 210 - left_margin - right_margin

    pdf.set_xy(left_margin, pdf.get_y() + 4)
    start_y = pdf.get_y()

    # Draw a light rectangle – we first compute approximate height by
    # writing to a temp PDF, but to keep things simple we'll just let
    # text flow and not clip; the light background is mainly decorative.
    # So just set a background colour for the area where we start text.
    # We'll slightly inset the text.
    pdf.set_fill_color(*BRAND_LIGHT_GREY)
    pdf.rect(left_margin - 1, start_y - 2, usable_width + 2, 0, "F")  # thin strip

    pdf.set_x(left_margin)
    pdf.multi_cell(usable_width, 7, handout_text)

    # Export PDF as bytes
    pdf_bytes = pdf.output(dest="S").encode("latin1")
    return pdf_bytes
