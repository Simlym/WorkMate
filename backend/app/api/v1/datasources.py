from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.datasource import Datasource

router = APIRouter()

SUPPORTED_TYPES = {"mysql", "postgresql", "mssql", "sqlite", "http_api", "shared"}


class DatasourceCreate(BaseModel):
    name: str
    type: str
    description: str = ""
    config: dict = {}
    enabled: bool = True


class DatasourceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    config: dict | None = None
    enabled: bool | None = None


def _ds_dict(ds: Datasource) -> dict:
    return {
        "id": ds.id,
        "name": ds.name,
        "type": ds.type,
        "description": ds.description,
        "config": ds.config,
        "enabled": ds.enabled,
        "created_at": ds.created_at.isoformat(),
    }


@router.get("")
async def list_datasources(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Datasource).order_by(Datasource.name))
    return [_ds_dict(ds) for ds in result.scalars().all()]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_datasource(
    body: DatasourceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.type not in SUPPORTED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported type. Supported: {sorted(SUPPORTED_TYPES)}")
    existing = await db.execute(select(Datasource).where(Datasource.name == body.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Datasource name already exists")

    ds = Datasource(**body.model_dump())
    db.add(ds)
    await db.commit()
    await db.refresh(ds)
    return _ds_dict(ds)


@router.get("/{ds_id}")
async def get_datasource(
    ds_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ds = await _get_or_404(ds_id, db)
    return _ds_dict(ds)


@router.patch("/{ds_id}")
async def update_datasource(
    ds_id: int,
    body: DatasourceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ds = await _get_or_404(ds_id, db)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(ds, field, value)
    await db.commit()
    await db.refresh(ds)
    return _ds_dict(ds)


@router.delete("/{ds_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_datasource(
    ds_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ds = await _get_or_404(ds_id, db)
    await db.delete(ds)
    await db.commit()


@router.post("/{ds_id}/test")
async def test_datasource(
    ds_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Test connectivity for the datasource."""
    ds = await _get_or_404(ds_id, db)
    result = await _test_connection(ds)
    return result


async def _test_connection(ds: Datasource) -> dict:
    if ds.type in {"mysql", "postgresql", "mssql", "sqlite"}:
        try:
            import sqlalchemy
            from sqlalchemy.ext.asyncio import create_async_engine

            url = ds.config.get("url") or _build_url(ds)
            engine = create_async_engine(url, pool_pre_ping=True)
            async with engine.connect() as conn:
                await conn.execute(sqlalchemy.text("SELECT 1"))
            await engine.dispose()
            return {"success": True, "message": "连接成功"}
        except Exception as exc:
            return {"success": False, "message": str(exc)}

    if ds.type == "http_api":
        try:
            import httpx
            url = ds.config.get("url", "")
            if not url:
                return {"success": False, "message": "缺少 url 配置"}
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(url)
            return {"success": True, "message": f"HTTP {resp.status_code}"}
        except Exception as exc:
            return {"success": False, "message": str(exc)}

    return {"success": True, "message": "无需连接测试"}


def _build_url(ds: Datasource) -> str:
    cfg = ds.config
    driver_map = {
        "mysql": "mysql+aiomysql",
        "postgresql": "postgresql+asyncpg",
        "mssql": "mssql+aioodbc",
        "sqlite": "sqlite+aiosqlite",
    }
    driver = driver_map.get(ds.type, ds.type)
    host = cfg.get("host", "localhost")
    port = cfg.get("port", "")
    user = cfg.get("username", "")
    pwd = cfg.get("password", "")
    db_name = cfg.get("database", "")
    port_str = f":{port}" if port else ""
    return f"{driver}://{user}:{pwd}@{host}{port_str}/{db_name}"


async def _get_or_404(ds_id: int, db: AsyncSession) -> Datasource:
    result = await db.execute(select(Datasource).where(Datasource.id == ds_id))
    ds = result.scalar_one_or_none()
    if ds is None:
        raise HTTPException(status_code=404, detail="Datasource not found")
    return ds
