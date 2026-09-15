from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, case
from sqlalchemy.orm import Session
from datetime import date, datetime

from app.db.session import get_db
from app.db.models.inventory_transaction import InventoryTransaction, TransactionType
from app.db.models.medicine import Medicine
from app.db.models.supplier import Supplier
from app.db.models.user import User
from app.core.deps import require_role
from app.schemas.invoice import ProfitLossRow

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("/profit-loss", response_model=list[ProfitLossRow])
def profit_loss_report(
    from_date: date = Query(alias="from"),
    to_date: date = Query(alias="to"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("client_admin", "staff")),
):
    """
    Medicine-wise + supplier-wise profit/loss for the given date range.
    purchase_cost = sum(qty * unit_price) for 'purchase' transactions
    sale_revenue  = sum(qty * unit_price) for 'sale' transactions
    tax_paid      = sum(qty * unit_price * gst_percent / 100) on purchases
    profit        = sale_revenue - purchase_cost
    """
    start = datetime.combine(from_date, datetime.min.time())
    end = datetime.combine(to_date, datetime.max.time())

    rows = (
        db.query(
            Medicine.id.label("medicine_id"),
            Medicine.name.label("medicine_name"),
            func.coalesce(Supplier.name, "—").label("supplier_name"),
            func.sum(
                case(
                    (InventoryTransaction.type == TransactionType.purchase,
                     InventoryTransaction.quantity * InventoryTransaction.unit_price),
                    else_=0,
                )
            ).label("total_purchase_cost"),
            func.sum(
                case(
                    (InventoryTransaction.type == TransactionType.sale,
                     InventoryTransaction.quantity * InventoryTransaction.unit_price),
                    else_=0,
                )
            ).label("total_sale_revenue"),
            func.sum(
                case(
                    (InventoryTransaction.type == TransactionType.purchase,
                     InventoryTransaction.quantity * InventoryTransaction.unit_price * Medicine.gst_percent / 100),
                    else_=0,
                )
            ).label("total_tax_paid"),
        )
        .join(Medicine, Medicine.id == InventoryTransaction.medicine_id)
        .outerjoin(Supplier, Supplier.id == InventoryTransaction.supplier_id)
        .filter(
            Medicine.client_id == current_user.client_id,
            InventoryTransaction.created_at >= start,
            InventoryTransaction.created_at <= end,
        )
        .group_by(Medicine.id, Medicine.name, Supplier.name)
        .all()
    )

    return [
        ProfitLossRow(
            medicine_id=r.medicine_id,
            medicine_name=r.medicine_name,
            supplier_name=r.supplier_name,
            total_purchase_cost=float(r.total_purchase_cost or 0),
            total_sale_revenue=float(r.total_sale_revenue or 0),
            total_tax_paid=float(r.total_tax_paid or 0),
            profit=float((r.total_sale_revenue or 0) - (r.total_purchase_cost or 0)),
        )
        for r in rows
    ]
