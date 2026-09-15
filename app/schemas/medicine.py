from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from uuid import UUID
from datetime import date


class MedicineCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    name: str
    barcode: str
    gst_percent: float = 0
    threshold_qty: int = 10
    expiry_date: date | None = None


class MedicineOut(BaseModel):
    id: UUID
    name: str
    barcode: str
    gst_percent: float
    threshold_qty: int
    current_stock: int
    expiry_date: date | None

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )
