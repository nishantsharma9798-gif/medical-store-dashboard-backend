import uuid
from datetime import date
from sqlalchemy import String, Numeric, Integer, Date, ForeignKey
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Medicine(Base):
    __tablename__ = "medicines"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("clients.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    barcode: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    gst_percent: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    threshold_qty: Mapped[int] = mapped_column(Integer, default=10)
    current_stock: Mapped[int] = mapped_column(Integer, default=0)
    expiry_date: Mapped[date | None] = mapped_column(Date, nullable=True)
