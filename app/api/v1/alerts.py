from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.medicine import Medicine
from app.db.models.user import User
from app.core.deps import require_role
from app.services.prediction import predict_weekend_demand

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


@router.get("")
def get_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("client_admin", "staff")),
):
    medicine_ids = [m.id for m in db.query(Medicine.id).filter(Medicine.client_id == current_user.client_id)]
    return predict_weekend_demand(db, medicine_ids)
