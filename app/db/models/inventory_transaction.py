import uuid
import enum
from datetime import datetime
from sqlalchemy import Enum, Integer, Numeric, ForeignKey, DateTime, func
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class TransactionType(str, enum.Enum):
    purchase = "purchase"
    sale = "sale"


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    medicine_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("medicines.id"), nullable=False, index=True)
    type: Mapped[TransactionType] = mapped_column(Enum(TransactionType), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    supplier_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("suppliers.id"), nullable=True)
    invoice_id: Mapped[uuid.UUID | None] = mapped_column(Uuid(as_uuid=True), ForeignKey("invoices.id"), nullable=True)
    # indexed for the Friday rule-based prediction job (day-of-week aggregation)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
