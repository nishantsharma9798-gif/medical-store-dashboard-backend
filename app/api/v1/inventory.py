from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date, datetime

from app.db.session import get_db
from app.db.models.inventory_transaction import InventoryTransaction, TransactionType
from app.db.models.medicine import Medicine
from app.db.models.supplier import Supplier
from app.db.models.user import User
from app.core.deps import require_role
from app.schemas.inventory import TransactionCreate, TransactionOut

router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])


@router.post("/transactions", response_model=TransactionOut)
def create_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("client_admin", "staff")),
):
    medicine = db.get(Medicine, payload.medicine_id)
    if not medicine or medicine.client_id != current_user.client_id:
        raise HTTPException(status_code=404, detail="Medicine not found")
    if payload.quantity <= 0 or payload.unit_price < 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive and unit price cannot be negative")
    if payload.supplier_id:
        supplier = db.get(Supplier, payload.supplier_id)
        if not supplier or supplier.client_id != current_user.client_id:
            raise HTTPException(status_code=404, detail="Supplier not found")

    transaction = InventoryTransaction(
        medicine_id=payload.medicine_id,
        type=payload.type,
        quantity=payload.quantity,
        unit_price=payload.unit_price,
        supplier_id=payload.supplier_id,
    )

    # keep stock in sync — purchase adds, sale subtracts
    if transaction.type == TransactionType.purchase:
        medicine.current_stock += payload.quantity
    else:
        if medicine.current_stock < payload.quantity:
            raise HTTPException(status_code=400, detail="Not enough stock for this sale")
        medicine.current_stock -= payload.quantity

    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    # NOTE: invoice auto-generation hook goes here — call services/invoice_pdf.py
    # once the invoice + invoice_items rows are created for this transaction.

    return transaction


@router.get("/transactions", response_model=list[TransactionOut])
def list_transactions(
    from_date: date | None = Query(default=None, alias="from"),
    to_date: date | None = Query(default=None, alias="to"),
    medicine_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("client_admin", "staff")),
):
    query = db.query(InventoryTransaction).join(Medicine).filter(Medicine.client_id == current_user.client_id)
    if from_date:
        query = query.filter(InventoryTransaction.created_at >= datetime.combine(from_date, datetime.min.time()))
    if to_date:
        query = query.filter(InventoryTransaction.created_at <= datetime.combine(to_date, datetime.max.time()))
    if medicine_id:
        query = query.filter(InventoryTransaction.medicine_id == medicine_id)
    return query.order_by(InventoryTransaction.created_at.desc()).all()
