from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
from ..utils.permissions import require_role
from ..models import User

router = APIRouter(prefix="/logs", tags=["logs"])

@router.get("/", response_model=List[schemas.ActionLog])
def get_logs(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    return db.query(models.ActionLog).order_by(models.ActionLog.timestamp.desc()).all()
