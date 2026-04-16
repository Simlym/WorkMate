from fastapi import APIRouter

from app.api.v1 import auth, conversations, chat, skills, datasources, feishu, admin

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(skills.router, prefix="/skills", tags=["skills"])
api_router.include_router(datasources.router, prefix="/datasources", tags=["datasources"])
api_router.include_router(feishu.router, prefix="/feishu", tags=["feishu"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
