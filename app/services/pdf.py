from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML

env = Environment(
    loader=FileSystemLoader("app/invoice_templates"),
    autoescape=select_autoescape()
)

def render_invoice_pdf(context: dict, out_path: str):
    template = env.get_template("invoice.html")
    html = template.render(**context)
    HTML(string=html).write_pdf(out_path)
    return out_path
