from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import engine
from . import models
from app.routers import products, meals, users, auth,reports, logs
from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordBearer
from app.utils.auth import oauth2_scheme
from .tasks import app as celery_app
# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Kindergarten Meal Tracking System",
    description="A comprehensive system for managing kitchen inventory, meal tracking, and report generation.",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(products.router)
app.include_router(meals.router)
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(logs.router) 

app.include_router(reports.router)

@app.get("/")
def read_root():
    return {"message": "Kindergarten Meal Tracking System API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}



@app.get("/check-auth")
def check_auth(token: str = Depends(oauth2_scheme)):
    return {"token": token}



from fastapi import WebSocket, WebSocketDisconnect
from typing import Set

# WebSocket ulanishlarini boshqarish
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    async def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

# @router.websocket("/ws/inventory")
# async def websocket_inventory(websocket: WebSocket, db: Session = Depends(get_db)):
#     await manager.connect(websocket)
#     try:
#         while True:
#             await websocket.receive_text()  # Ulanishni tirik tutish
#             low_inventory = crud.check_low_inventory(db)
#             inventory = crud.get_products(db)
#             await manager.broadcast({
#                 "inventory": [
#                     {"id": p.id, "name": p.name, "current_weight": p.current_weight}
#                     for p in inventory
#                 ],
#                 "low_inventory": low_inventory
#             })
#     except WebSocketDisconnect:
#         manager.disconnect(websocket)