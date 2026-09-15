import uuid
import enum
from datetime import datetime
from sqlalchemy import Enum, String, ForeignKey, DateTime, func
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class AttachmentSource(str, enum.Enum):
    whatsapp = "whatsapp"
    manual_upload = "manual_upload"


class AttachmentStatus(str, enum.Enum):
    pending_review = "pending_review"
    linked = "linked"


class InvoiceAttachment(Base):
    """
    Raw invoice file (image/PDF) received from a supplier — via WhatsApp webhook
    or manual upload. Starts as pending_review; staff links it to a purchase
    transaction/invoice after confirming the details, at which point invoice_id
    is set and status becomes 'linked'.
    """
    __tablename__ = "invoice_attachments"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("clients.id"), nullable=False, index=True)
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("invoices.id"), nullable=True)
    source: Mapped[AttachmentSource] = mapped_column(Enum(AttachmentSource), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    whatsapp_message_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[AttachmentStatus] = mapped_column(Enum(AttachmentStatus), default=AttachmentStatus.pending_review)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
