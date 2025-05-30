from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas
from ..database import get_db
from ..utils.permissions import require_role
from ..models import User
from ..utils.auth import get_current_user
from datetime import datetime, timezone
router = APIRouter(prefix="/products", tags=["products"])

@router.post("/", response_model=schemas.Product)
def create_product(
    product: schemas.ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["manager", "admin"]))
):
    if product.current_weight < 0:
        raise HTTPException(status_code=400, detail="Joriy og'irlik manfiy bo'lishi mumkin emas")
    if product.delivery_date and product.delivery_date > datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Yetkazib berish sanasi kelajakda bo'lishi mumkin emas")
    return crud.create_product(db=db, product=product)

@router.get("/", response_model=List[schemas.Product])
def read_products(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return crud.get_products(db, skip=skip, limit=limit)


@router.put("/{product_id}", response_model=schemas.Product)
async def update_product(  # async sifatida belgilandi
    product_id: int,
    product: schemas.ProductUpdate,
    current_user: User = Depends(require_role(["manager", "admin"])),
    db: Session = Depends(get_db)
):
    # Validatsiyalar
    if product.current_weight < 0:
        raise HTTPException(status_code=400, detail="Joriy og'irlik manfiy bo'lishi mumkin emas")
    if product.delivery_date and product.delivery_date > datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Yetkazib berish sanasi kelajakda bo'lishi mumkin emas")
    
    
    # Mahsulotni yangilash
    db_product = await crud.update_product(db, product_id=product_id, product=product)  # await ishlatildi
    if db_product is None:
        raise HTTPException(status_code=404, detail="Mahsulot topilmadi")
    return db_product
@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    current_user: User = Depends(require_role(["manager", "admin"])),
    db: Session = Depends(get_db)
):
    db_product = crud.delete_product(db, product_id=product_id)
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}


@router.get("/low-inventory", response_model=List[dict])
def get_low_inventory(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["manager", "admin"]))
):
    low_inventory = crud.check_low_inventory(db)
    if not low_inventory:
        return []
    return low_inventory