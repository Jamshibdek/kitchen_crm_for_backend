from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from . import models, schemas
from passlib.context import CryptContext
from typing import List, Optional
from .utils.websocket import manager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from datetime import timezone, datetime
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# User CRUD
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    log_action(db, user_id=None, action="create", target_table="users", target_id=db_user.id, details=f"Created user: {db_user.username}")
    return db_user


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)

# Product CRUD
def get_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Product).offset(skip).limit(limit).all()

def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()



from datetime import datetime, timezone

def create_product(db: Session, product: schemas.ProductCreate, user_id: Optional[int] = None):


    db_product = models.Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    log_action(db, user_id, "create", "products", db_product.id, f"Product {db_product.name} added.")
    return db_product





        
        
        # WebSocket ...


def delete_product(db: Session, product_id: int, user_id: Optional[int] = None):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if db_product:
        db.delete(db_product)
        db.commit()

        log_action(db, user_id, "delete", "products", product_id, f"Deleted product {db_product.name}")
    return db_product


# Meal CRUD
def get_meals(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Meal).offset(skip).limit(limit).all()

def get_meal(db: Session, meal_id: int):
    return db.query(models.Meal).filter(models.Meal.id == meal_id).first()

def create_meal(db: Session, meal: schemas.MealCreate, user_id: Optional[int] = None):
    db_meal = models.Meal(name=meal.name, description=meal.description)
    db.add(db_meal)
    db.commit()
    db.refresh(db_meal)
    
    # Add ingredients
    for ingredient in meal.ingredients:
        db_ingredient = models.MealIngredient(
            meal_id=db_meal.id,
            product_id=ingredient.product_id,
            quantity_needed=ingredient.quantity_needed
        )
        db.add(db_ingredient)
    
    db.commit()
    db.refresh(db_meal)
    log_action(db, user_id, "create", "Meals", db_meal.id, f"Meal {db_meal.name} added.")
    return db_meal

async def update_product(db: Session, product_id: int, product: schemas.ProductUpdate, user_id: Optional[int] = None):
    db_product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if db_product:
        update_data = product.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_product, key, value)
        db.commit()
        db.refresh(db_product)
        
        # WebSocket tarqatish
        low_inventory = check_low_inventory(db)
        inventory = get_products(db)
        await manager.broadcast({
            "inventory": [
                {"id": p.id, "name": p.name, "current_weight": p.current_weight}
                for p in inventory
            ],
            "low_inventory": low_inventory
        })
        log_action(db, user_id, "update", "products", db_product.id, f"Updated product {db_product.name}")
    return db_product

def delete_meal(db: Session, meal_id: int, user_id:int):
    db_meal = db.query(models.Meal).filter(models.Meal.id == meal_id).first()
    if db_meal:
        # Delete ingredients first
        db.query(models.MealIngredient).filter(models.MealIngredient.meal_id == meal_id).delete()
        db.delete(db_meal)
        db.commit()
        log_action(db, user_id, "delete", "meal", db_meal.id, f"Delete meal {db_meal.name}")
    return db_meal

# Portion Estimation
def calculate_portion_estimations(db: Session):
    meals = db.query(models.Meal).all()
    estimations = []
    
    for meal in meals:
        min_portions = float('inf')
        limiting_ingredient = ""
        
        for ingredient in meal.ingredients:
            product = ingredient.product
            if product.current_weight > 0 and ingredient.quantity_needed > 0:
                possible_portions = int(product.current_weight / ingredient.quantity_needed)
                if possible_portions < min_portions:
                    min_portions = possible_portions
                    limiting_ingredient = product.name
        
        if min_portions == float('inf'):
            min_portions = 0
            limiting_ingredient = "No ingredients available"
        
        estimations.append(schemas.PortionEstimation(
            meal_id=meal.id,
            meal_name=meal.name,
            max_portions=min_portions,
            limiting_ingredient=limiting_ingredient
        ))
    
    return estimations

# Meal Serving
async def serve_meal(db: Session, meal_id: int, user_id: int, portions: int = 1):
    meal = db.query(models.Meal).filter(models.Meal.id == meal_id).first()
    if not meal:
        return None, "Ovqat topilmadi"
    
    if portions <= 0:
        return None, "Porsiyalar soni musbat bo'lishi kerak"

    # Ingredientlar yetarliligini tekshirish
    insufficient_ingredients = []
    for ingredient in meal.ingredients:
        needed = ingredient.quantity_needed * portions
        if ingredient.product.current_weight < needed:
            insufficient_ingredients.append({
                "ingredient": ingredient.product.name,
                "needed": needed,
                "available": ingredient.product.current_weight
            })
    
    if insufficient_ingredients:
        return None, f"Yetarli ingredientlar yo'q: {insufficient_ingredients}"
    
    # Ingredientlarni ayirish
    for ingredient in meal.ingredients:
        needed = ingredient.quantity_needed * portions
        ingredient.product.current_weight -= needed
    
    # Ovqat berishni jurnalga yozish
    meal_log = models.MealLog(
        meal_id=meal_id,
        user_id=user_id,
        portions_served=portions
    )
    db.add(meal_log)
    db.commit()
    db.refresh(meal_log)
    log_action(db, user_id, "serve", "meals", meal_id, f"Served meal ID {meal_id} with {portions} portions.")
    # WebSocket tarqatish
    low_inventory = check_low_inventory(db)
    inventory = get_products(db)
    await manager.broadcast({
        "inventory": [
            {"id": p.id, "name": p.name, "current_weight": p.current_weight}
            for p in inventory
        ],
        "low_inventory": low_inventory
    })
    
    return meal_log, "Ovqat muvaffaqiyatli berildi" if not low_inventory else f"Ovqat muvaffaqiyatli berildi. Ogohlantirish: {low_inventory} uchun ombor kam"
    
  

def get_all_users(db: Session):
    return db.query(models.User).all()



from datetime import datetime, timedelta

def get_monthly_summary_report(db: Session):
    # Bu oy boshi
    now = datetime.utcnow()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Berilgan porsiyalar soni
    total_served = db.query(models.MealLog).filter(
        models.MealLog.served_at >= start_of_month
    ).with_entities(func.sum(models.MealLog.portions_served)).scalar() or 0

    # Max berilishi mumkin bo‘lgan porsiyalar (current inventory asosida)
    portion_estimations = calculate_portion_estimations(db)
    total_possible = sum(est.max_portions for est in portion_estimations)

    # Farq
    difference = total_possible - total_served
    if total_possible == 0:
        difference_rate = 0
    else:
        difference_rate = round((difference / total_possible) * 100, 2)

    misuse_flag = difference_rate > 15
    return {
        "month": now.strftime("%B %Y"),
        "portions_served": total_served,
        "portions_possible": total_possible,
        "difference_rate": difference_rate,
        "misuse_flag": misuse_flag
    }

def check_low_inventory(db: Session):
    """Ombordagi mahsulotlarning miqdori threshold_warning dan past bo'lsa, ro'yxatni qaytaradi."""
    products = db.query(models.Product).filter(
        models.Product.current_weight <= models.Product.threshold_warning
    ).all()
    return [
        {
            "product_id": p.id,
            "name": p.name,
            "current_weight": p.current_weight,
            "threshold_warning": p.threshold_warning
        }
        for p in products
    ]


def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return None
    update_data = user_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(user, key, value)
    db.commit()
    db.refresh(user)
    log_action(db, user_id, "update", "User", user_id, f"Deleted User {user_id}")
    return user

def delete_user(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        log_action(db, user_id, "delete", "user", user_id, f"Deleted user {user_id}")
        db.delete(user)
        db.commit()
        
    return user


def update_meal(db: Session, meal_id: int, meal: schemas.MealUpdate,  user_id: Optional[int] = None):
    db_meal = db.query(models.Meal).filter(models.Meal.id == meal_id).first()
    if not db_meal:
        return None

    if meal.name is not None:
        db_meal.name = meal.name
    if meal.description is not None:
        db_meal.description = meal.description

    # Ingredientlar yangilanayotgan bo‘lsa
    if meal.ingredients is not None:
        db.query(models.MealIngredient).filter(models.MealIngredient.meal_id == meal_id).delete()

        for ingredient in meal.ingredients:
            new_ingredient = models.MealIngredient(
                meal_id=meal_id,
                product_id=ingredient.product_id,
                quantity_needed=ingredient.quantity_needed
            )
            db.add(new_ingredient)

    db.commit()
    db.refresh(db_meal)
    log_action(db, user_id, "update", "meals", meal_id, f"Updated meal ID {meal_id}")
    return db_meal


def log_action(
    db: Session,
    user_id: Optional[int],
    action: str,
    target_table: str,
    target_id: int,
    details: Optional[str] = None
):
    log = models.ActionLog(
        user_id=user_id,
        action=action,
        target_table=target_table,
        target_id=target_id,
        details=details or ""
    )
    db.add(log)
    db.commit()
