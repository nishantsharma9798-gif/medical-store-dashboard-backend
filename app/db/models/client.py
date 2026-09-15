import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy import JSON
from sqlalchemy import Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    enabled_apps: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
