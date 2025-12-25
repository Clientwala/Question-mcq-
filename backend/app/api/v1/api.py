"""
API v1 Router.

Combines all API v1 endpoints.
"""
from fastapi import APIRouter
from app.api.v1.endpoints import jobs

api_router = APIRouter()

# Include job endpoints
api_router.include_router(jobs.router)

# Future: Add more endpoint routers here
# api_router.include_router(users.router)
# api_router.include_router(admin.router)
