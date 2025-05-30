from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    role = Column(String, default="cook")  # admin, manager, cook
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationship
    meal_logs = relationship("MealLog", back_populates="user")

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    current_weight = Column(Float)  # in grams
    unit = Column(String, default="grams")
    delivery_date = Column(DateTime(timezone=True))
    threshold_warning = Column(Float, default=100.0)  # warning when below this amount
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    meal_ingredients = relationship("MealIngredient", back_populates="product")

class Meal(Base):
    __tablename__ = "meals"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    ingredients = relationship("MealIngredient", back_populates="meal")
    meal_logs = relationship("MealLog", back_populates="meal")

class MealIngredient(Base):
    __tablename__ = "meal_ingredients"
    
    id = Column(Integer, primary_key=True, index=True)
    meal_id = Column(Integer, ForeignKey("meals.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity_needed = Column(Float)  # in grams
    
    # Relationships
    meal = relationship("Meal", back_populates="ingredients")
    product = relationship("Product", back_populates="meal_ingredients")

class MealLog(Base):
    __tablename__ = "meal_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    meal_id = Column(Integer, ForeignKey("meals.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    served_at = Column(DateTime(timezone=True), server_default=func.now())
    portions_served = Column(Integer, default=1)
    notes = Column(Text)
    
    # Relationships
    meal = relationship("Meal", back_populates="meal_logs")
    user = relationship("User", back_populates="meal_logs")

# =============================================================================



class ActionLog(Base):
    __tablename__ = "action_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    action = Column(String, index=True)  # create, update, delete
    target_table = Column(String)
    target_id = Column(Integer)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    details = Column(Text)

    user = relationship("User")
