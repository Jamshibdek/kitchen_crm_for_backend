from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

# User Schemas
class UserBase(BaseModel):
    username: str
    email: str
    full_name: str
    role: str = "cook"

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


# Product Schemas
class ProductBase(BaseModel):
    name: str
    current_weight: float
    unit: str = "grams"
    threshold_warning: float = 100.0

class ProductCreate(ProductBase):
    delivery_date: Optional[datetime] = None

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    current_weight: Optional[float] = None
    unit: Optional[str] = None
    delivery_date: Optional[datetime] = None
    threshold_warning: Optional[float] = None

class Product(ProductBase):
    id: int
    delivery_date: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# Meal Ingredient Schemas
class MealIngredientBase(BaseModel):
    product_id: int
    quantity_needed: float

class MealIngredientCreate(MealIngredientBase):
    pass

class MealIngredient(MealIngredientBase):
    id: int
    product: Optional[Product] = None   # ✅ optional qilib qo‘ydik

    class Config:
        from_attributes = True


# Meal Schemas
class MealBase(BaseModel):
    name: str
    description: Optional[str] = None

class MealCreate(MealBase):
    ingredients: List[MealIngredientCreate]

class MealUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    ingredients: Optional[List[MealIngredientCreate]] = None

class Meal(MealBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime]
    ingredients: Optional[List[MealIngredient]] = None  # ✅ bu ham optional

    class Config:
        from_attributes = True


# Meal Log Schemas
class MealLogBase(BaseModel):
    meal_id: int
    portions_served: int = 1
    notes: Optional[str] = None

class MealLogCreate(MealLogBase):
    pass

class MealLog(MealLogBase):
    id: int
    user_id: Optional[int] = None
    meal_id: Optional[int] = None
    served_at: Optional[datetime] = None
    meal: Optional[Meal] = None
    user: Optional[User] = None

    class Config:
        from_attributes = True



# Portion Estimation Schema
class PortionEstimation(BaseModel):
    meal_id: int
    meal_name: str
    max_portions: int
    limiting_ingredient: str




class ActionLog(BaseModel):
    id: int
    user_id: Optional[int]
    action: str
    target_table: str
    target_id: int
    timestamp: datetime
    details: Optional[str] = None

    class Config:
        from_attributes = True
