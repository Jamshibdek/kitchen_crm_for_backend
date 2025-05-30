from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..models import User
from ..utils.permissions import require_role
from ..database import get_db
from .. import crud

router = APIRouter(prefix="/reports", tags=["reports"])

@router.get("/summary")
def monthly_summary(
    current_user: User = Depends(require_role(["admin"])),
    db: Session = Depends(get_db)
):
    report = crud.get_monthly_summary_report(db)
    if report["misuse_flag"]:
        report["alert"] = "Ogohlantirish: Potensial suiste'mol aniqlandi (farq > 15%)"
    return report