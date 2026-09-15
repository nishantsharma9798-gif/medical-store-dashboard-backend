from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from uuid import UUID


class SupplierCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    name: str
    whatsapp_number: str
    mapped_medicine_ids: list[UUID] = []


class SupplierOut(BaseModel):
    id: UUID
    name: str
    whatsapp_number: str
    mapped_medicine_ids: list[UUID]

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )


class OrderCreate(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
    medicine_id: UUID
    supplier_id: UUID
    requested_qty: int


class OrderOut(BaseModel):
    id: UUID
    medicine_id: UUID
    supplier_id: UUID
    requested_qty: int
    status: str

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )
