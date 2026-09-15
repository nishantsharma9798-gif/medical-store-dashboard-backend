import os
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from app.core.config import settings

_env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")))


def generate_invoice_pdf(invoice, items, client_name: str) -> str:
    """
    Renders invoice_template.html with the invoice + items data, converts it to
    PDF via WeasyPrint, and returns the saved file path. GST is split into
    CGST/SGST (intra-state assumption) in the template itself.
    """
    template = _env.get_template("invoice_template.html")
    html_content = template.render(invoice=invoice, items=items, client_name=client_name)

    os.makedirs(settings.storage_dir, exist_ok=True)
    file_path = os.path.join(settings.storage_dir, f"{invoice.invoice_no}.pdf")
    HTML(string=html_content).write_pdf(file_path)

    return file_path
