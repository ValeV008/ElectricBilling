"""PDF generation services."""

from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

env = Environment(
    loader=FileSystemLoader("app/templates"), autoescape=select_autoescape()
)


def render_invoice_pdf_bytes(context: dict) -> bytes | None:
    """Render invoice template to PDF bytes (no file I/O)."""
    template = env.get_template("invoices/invoice.html")
    html = template.render(**context)
    return HTML(string=html).write_pdf()
