from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.medicine import Medicine
from app.db.models.user import User
from app.core.deps import require_role
from app.schemas.medicine import MedicineCreate, MedicineOut

router = APIRouter(prefix="/api/v1/medicines", tags=["medicines"])


@router.get("", response_model=list[MedicineOut])
def list_medicines(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("client_admin", "staff")),
):
    return db.query(Medicine).filter(Medicine.client_id == current_user.client_id).all()


@router.get("/{barcode}", response_model=MedicineOut)
def get_by_barcode(
    barcode: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("client_admin", "staff")),
):
    medicine = (
        db.query(Medicine)
        .filter(Medicine.client_id == current_user.client_id, Medicine.barcode == barcode)
        .first()
    )
    if not medicine:
        raise HTTPException(status_code=404, detail="Medicine not found for this barcode")
    return medicine


@router.post("", response_model=MedicineOut)
def create_medicine(
    payload: MedicineCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("client_admin", "staff")),
):
    existing = (
        db.query(Medicine)
        .filter(Medicine.client_id == current_user.client_id, Medicine.barcode == payload.barcode)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A medicine with this barcode already exists")

    medicine = Medicine(client_id=current_user.client_id, **payload.model_dump())
    db.add(medicine)
    db.commit()
    db.refresh(medicine)
    return medicine
