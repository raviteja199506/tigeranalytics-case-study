from fastapi import APIRouter

from app.api.routes import ingestions, pricing

api_router = APIRouter()
api_router.include_router(ingestions.router)
api_router.include_router(pricing.router)
