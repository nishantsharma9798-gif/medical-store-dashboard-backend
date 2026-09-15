from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.supplier import Supplier
from app.db.models.medicine import Medicine
from app.db.models.user import User
from app.core.deps import require_role
from app.schemas.supplier import SupplierCreate, SupplierOut

router = APIRouter(prefix="/api/v1/suppliers", tags=["suppliers"])


@router.get("", response_model=list[SupplierOut])
def list_suppliers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("client_admin", "staff")),
):
    return db.query(Supplier).filter(Supplier.client_id == current_user.client_id).all()


@router.post("", response_model=SupplierOut)
def create_supplier(
    payload: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("client_admin", "staff")),
):
    medicine_count = (
        db.query(Medicine.id)
        .filter(Medicine.client_id == current_user.client_id, Medicine.id.in_(payload.mapped_medicine_ids))
        .count()
        if payload.mapped_medicine_ids
        else 0
    )
    if medicine_count != len(set(payload.mapped_medicine_ids)):
        raise HTTPException(status_code=400, detail="One or more mapped medicines were not found")

    supplier = Supplier(
        client_id=current_user.client_id,
        name=payload.name,
        whatsapp_number=payload.whatsapp_number,
        mapped_medicine_ids=[str(mid) for mid in payload.mapped_medicine_ids],
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier
