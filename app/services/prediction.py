from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.models.inventory_transaction import InventoryTransaction, TransactionType
from app.db.models.medicine import Medicine


def predict_weekend_demand(db: Session, client_medicine_ids: list) -> list[dict]:
    """
    Rule-based prediction: for each medicine, average the quantity sold on the
    same weekday over the last 4 occurrences, then compare against current stock.
    Returns medicines predicted to run low, with a suggested reorder quantity.

    NOTE: intentionally simple for Phase 1. Swap this function's internals for a
    proper time-series model (e.g. Prophet) in Phase 2 without touching callers.
    """
    results = []
    today = datetime.utcnow()
    target_weekday = (today + timedelta(days=(5 - today.weekday()) % 7)).weekday()  # upcoming Saturday
    lookback_start = today - timedelta(weeks=8)

    for medicine_id in client_medicine_ids:
        medicine = db.get(Medicine, medicine_id)
        if not medicine:
            continue

        sales = db.scalars(
            select(InventoryTransaction).where(
                InventoryTransaction.medicine_id == medicine_id,
                InventoryTransaction.type == TransactionType.sale,
                InventoryTransaction.created_at >= lookback_start,
            )
        ).all()

        same_weekday_qty = [s.quantity for s in sales if s.created_at.weekday() == target_weekday]
        if not same_weekday_qty:
            continue

        predicted_demand = round(sum(same_weekday_qty) / len(same_weekday_qty))

        if medicine.current_stock < predicted_demand or medicine.current_stock <= medicine.threshold_qty:
            suggested_qty = max(predicted_demand - medicine.current_stock, medicine.threshold_qty)
            results.append(
                {
                    "medicine_id": medicine.id,
                    "medicine_name": medicine.name,
                    "predicted_demand": predicted_demand,
                    "current_stock": medicine.current_stock,
                    "suggested_order_qty": suggested_qty,
                }
            )

    return results
