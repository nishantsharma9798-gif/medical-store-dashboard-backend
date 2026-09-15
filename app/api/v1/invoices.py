import os
import shutil
import uuid as uuid_lib
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from datetime import date, datetime

from app.db.session import get_db
from app.db.models.invoice import Invoice
from app.db.models.invoice_attachment import InvoiceAttachment, AttachmentSource
from app.db.models.user import User
from app.core.deps import require_role
from app.core.config import settings
from app.schemas.invoice import InvoiceOut
from app.services.whatsapp import send_whatsapp

router = APIRouter(prefix="/api/v1/invoices", tags=["invoices"])


@router.get("", response_model=list[InvoiceOut])
def list_invoices(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    type: str | None = None,
    party: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("client_admin", "staff")),
):
    query = db.query(Invoice).filter(Invoice.client_id == current_user.client_id)
    if from_date:
        query = query.filter(Invoice.created_at >= datetime.combine(from_date, datetime.min.time()))
    if to_date:
        query = query.filter(Invoice.created_at <= datetime.combine(to_date, datetime.max.time()))
    if type:
        query = query.filter(Invoice.type == type)
    if party:
        query = query.filter(Invoice.party_name.ilike(f"%{party}%"))
    return query.order_by(Invoice.created_at.desc()).all()


@router.get("/{invoice_id}", response_model=InvoiceOut)
def get_invoice(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("client_admin", "staff")),
):
    invoice = db.get(Invoice, invoice_id)
    if not invoice or invoice.client_id != current_user.client_id:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice


@router.get("/{invoice_id}/pdf")
def download_invoice_pdf(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("client_admin", "staff")),
):
    invoice = db.get(Invoice, invoice_id)
    if not invoice or not invoice.pdf_path or not os.path.exists(invoice.pdf_path):
        raise HTTPException(status_code=404, detail="Invoice PDF not found")
    return FileResponse(invoice.pdf_path, media_type="application/pdf")


@router.post("/{invoice_id}/share-whatsapp")
async def share_invoice_on_whatsapp(
    invoice_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("client_admin", "staff")),
):
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    await send_whatsapp(to="<customer_number>", template_name="invoice_share", params={"invoice_no": invoice.invoice_no})
    return {"detail": "Invoice shared"}


@router.post("/attachments")
async def upload_purchase_invoice(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("client_admin", "staff")),
):
    """
    Manual upload path for a supplier invoice that didn't arrive via WhatsApp.
    Stored as pending_review — staff links it to a purchase entry afterwards,
    same as WhatsApp-received attachments (see services/whatsapp.py).
    """
    os.makedirs(settings.storage_dir, exist_ok=True)
    file_name = f"{uuid_lib.uuid4()}_{file.filename}"
    file_path = os.path.join(settings.storage_dir, file_name)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    attachment = InvoiceAttachment(
        client_id=current_user.client_id,
        source=AttachmentSource.manual_upload,
        file_url=file_path,
    )
    db.add(attachment)
    db.commit()
    return {"detail": "Uploaded, pending review", "attachment_id": str(attachment.id)}
