from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from uuid import UUID
from datetime import datetime
from app.db.models.inventory_transaction import TransactionType


class TransactionCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    medicine_id: UUID
    type: TransactionType
    quantity: int
    unit_price: float
    supplier_id: UUID | None = None


class TransactionOut(BaseModel):
    id: UUID
    medicine_id: UUID
    type: str
    quantity: int
    unit_price: float
    supplier_id: UUID | None
    invoice_id: UUID | None
    created_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )
