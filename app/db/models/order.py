import uuid
import enum
from datetime import datetime
from sqlalchemy import Enum, Integer, ForeignKey, DateTime, func
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class OrderStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    rejected = "rejected"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    medicine_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("medicines.id"), nullable=False)
    supplier_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("suppliers.id"), nullable=False)
    requested_qty: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.pending)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
