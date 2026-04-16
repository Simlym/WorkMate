from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.config import settings
from app.database import init_db, AsyncSessionLocal
from app.api.v1.router import api_router
from app.mcp.server import get_mcp_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await _load_enabled_skills()
    yield


async def _load_enabled_skills():
    from app.models.skill import Skill
    from app.services.skill_loader import reload_skills_from_store

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Skill.name, Skill.package_path, Skill.entry_point).where(Skill.enabled == True)
        )
        rows = result.all()

    reload_skills_from_store([(r.name, r.package_path, r.entry_point) for r in rows])


app = FastAPI(title="WorkMate API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

# Mount MCP server at /mcp (Dify connects here)
app.mount("/mcp", get_mcp_app())


@app.get("/health")
async def health():
    return {"status": "ok"}
