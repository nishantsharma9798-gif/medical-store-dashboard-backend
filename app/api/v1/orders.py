from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.order import Order, OrderStatus
from app.db.models.supplier import Supplier
from app.db.models.medicine import Medicine
from app.db.models.user import User
from app.core.deps import require_role
from app.schemas.supplier import OrderCreate, OrderOut
from app.services.whatsapp import send_whatsapp, handle_incoming_webhook

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])


@router.post("", response_model=OrderOut)
async def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("client_admin", "staff")),
):
    supplier = db.get(Supplier, payload.supplier_id)
    if not supplier or supplier.client_id != current_user.client_id:
        raise HTTPException(status_code=404, detail="Supplier not found")
    medicine = db.get(Medicine, payload.medicine_id)
    if not medicine or medicine.client_id != current_user.client_id:
        raise HTTPException(status_code=404, detail="Medicine not found")
    if payload.requested_qty <= 0:
        raise HTTPException(status_code=400, detail="Requested quantity must be positive")

    order = Order(
        medicine_id=payload.medicine_id,
        supplier_id=payload.supplier_id,
        requested_qty=payload.requested_qty,
        status=OrderStatus.pending,
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    await send_whatsapp(
        to=supplier.whatsapp_number,
        template_name="order_request",
        params={"quantity": payload.requested_qty, "order_id": str(order.id)},
    )

    return order


@router.get("", response_model=list[OrderOut])
def list_orders(
    status_filter: str | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("client_admin", "staff")),
):
    query = db.query(Order).join(Supplier).filter(Supplier.client_id == current_user.client_id)
    if status_filter:
        query = query.filter(Order.status == status_filter)
    return query.all()


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    Provider (AiSensy/Gupshup) posts here on: (a) supplier reply confirming/
    rejecting an order, or (b) supplier sending an invoice file. Payload shape
    is provider-specific — flesh this out once the provider is finalized.
    """
    payload = await request.json()
    result = await handle_incoming_webhook(payload)
    return result
