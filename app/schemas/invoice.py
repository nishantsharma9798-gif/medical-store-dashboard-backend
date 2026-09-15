from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel
from uuid import UUID
from datetime import datetime


class InvoiceItemOut(BaseModel):
    medicine_id: UUID
    quantity: int
    unit_price: float
    gst_percent: float

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )


class InvoiceOut(BaseModel):
    id: UUID
    invoice_no: str
    type: str
    party_name: str
    subtotal: float
    gst_amount: float
    total: float
    pdf_path: str | None
    created_at: datetime
    items: list[InvoiceItemOut]

    model_config = ConfigDict(
        from_attributes=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )


class ProfitLossRow(BaseModel):
    medicine_id: UUID
    medicine_name: str
    supplier_name: str
    total_purchase_cost: float
    total_sale_revenue: float
    total_tax_paid: float
    profit: float

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
