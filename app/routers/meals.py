from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas
from ..database import get_db
from fastapi import APIRouter, Depends
from ..utils.permissions import require_role
from ..models import User
from ..utils.auth import get_current_user
from .. import models
from ..models import User, MealLog
from sqlalchemy.orm import joinedload

router = APIRouter(prefix="/meals", tags=["meals"])

@router.get("/", response_model=List[schemas.Meal])
def read_meals(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # ⛔ endi token talab qiladi
):
    return crud.get_meals(db, skip=skip, limit=limit)


@router.post("/", response_model=schemas.Meal)
def create_meal(
    meal: schemas.MealCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["manager", "admin"]))
):
    return crud.create_meal(db=db, meal=meal)

@router.put("/{meal_id}", response_model=schemas.Meal)
def update_meal(
    meal_id: int,
    meal: schemas.MealUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["manager", "admin"]))
):
    db_meal = crud.update_meal(db, meal_id=meal_id, meal=meal)
    if db_meal is None:
        raise HTTPException(status_code=404, detail="Meal not found")
    return db_meal

@router.delete("/{meal_id}")
def delete_meal(
    meal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["manager", "admin"]))
):
    db_meal = crud.delete_meal(db, meal_id=meal_id)
    if db_meal is None:
        raise HTTPException(status_code=404, detail="Meal not found")
    return {"message": "Meal deleted successfully"}

@router.get("/estimations/portions", response_model=List[schemas.PortionEstimation])
def get_portion_estimations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # login bo'lishi kerak
):
    return crud.calculate_portion_estimations(db)

@router.post("/{meal_id}/serve")
async def serve_meal(  # async sifatida belgilandi
    meal_id: int,
    portions: int = 1,
    current_user: User = Depends(require_role(["cook"])),
    db: Session = Depends(get_db)
):
    meal_log, message = await crud.serve_meal(db, meal_id=meal_id, user_id=current_user.id, portions=portions)  # await ishlatildi
    if meal_log is None:
        raise HTTPException(status_code=400, detail=message)
    return {"message": message, "meal_log": meal_log}







# 1. LOGS ENDPOINT BIRINCHI
@router.get("/logs", response_model=List[schemas.MealLog])
def get_meal_logs(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["manager", "admin"]))
):
    logs = db.query(models.MealLog)\
        .options(joinedload(models.MealLog.meal), joinedload(models.MealLog.user))\
        .offset(skip).limit(limit).all()
    return logs

# 2. UNDAN KEYIN DYNAMIC ROUTE
@router.get("/{meal_id}", response_model=schemas.Meal)
def read_meal(
    meal_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_meal = crud.get_meal(db, meal_id=meal_id)
    if db_meal is None:
        raise HTTPException(status_code=404, detail="Meal not found")
    return db_meal
