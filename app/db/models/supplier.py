import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy import JSON
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("clients.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    whatsapp_number: Mapped[str] = mapped_column(String(20), nullable=False)
    mapped_medicine_ids: Mapped[list] = mapped_column(JSON, default=list)
