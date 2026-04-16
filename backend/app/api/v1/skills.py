import shutil
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.models.skill import Skill
from app.services.skill_loader import (
    install_skill_package,
    load_and_register,
    unload_skill,
    SKILLS_STORE,
)

router = APIRouter()


def _skill_dict(s: Skill) -> dict:
    return {
        "id": s.id,
        "name": s.name,
        "version": s.version,
        "description": s.description,
        "enabled": s.enabled,
        "entry_point": s.entry_point,
        "installed_at": s.installed_at.isoformat(),
    }


@router.get("")
async def list_skills(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Skill).order_by(Skill.name))
    return [_skill_dict(s) for s in result.scalars().all()]


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_skill(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a skill zip package, install it, and register the tool."""
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip skill packages are supported")

    # Save upload to a temp file
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp:
        tmp.write(await file.read())
        tmp_path = Path(tmp.name)

    try:
        meta, skill_dir = install_skill_package(tmp_path)
    except (KeyError, ValueError) as exc:
        tmp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Invalid skill package: {exc}")
    except RuntimeError as exc:
        tmp_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        tmp_path.unlink(missing_ok=True)

    # Check for duplicate
    existing = await db.execute(select(Skill).where(Skill.name == meta.name))
    if existing.scalar_one_or_none():
        # Re-upload: unload old, overwrite DB record
        unload_skill(meta.name)
        skill_row = (await db.execute(select(Skill).where(Skill.name == meta.name))).scalar_one()
        skill_row.version = meta.version
        skill_row.description = meta.description
        skill_row.entry_point = meta.entry
        skill_row.package_path = str(skill_dir)
        skill_row.enabled = True
    else:
        skill_row = Skill(
            name=meta.name,
            version=meta.version,
            description=meta.description,
            entry_point=meta.entry,
            package_path=str(skill_dir),
            enabled=True,
        )
        db.add(skill_row)

    await db.commit()
    await db.refresh(skill_row)

    # Load into registry (this also triggers MCP registration via callback)
    try:
        load_and_register(skill_dir, meta.entry, meta.name)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Skill loaded to disk but failed to activate: {exc}")

    return _skill_dict(skill_row)


@router.patch("/{skill_id}/enable")
async def enable_skill(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    skill_row = await _get_skill_or_404(skill_id, db)
    if not skill_row.enabled:
        skill_dir = Path(skill_row.package_path) if skill_row.package_path else SKILLS_STORE / skill_row.name
        try:
            load_and_register(skill_dir, skill_row.entry_point, skill_row.name)
        except Exception as exc:
            raise HTTPException(status_code=500, detail=str(exc))
        skill_row.enabled = True
        await db.commit()
        await db.refresh(skill_row)
    return _skill_dict(skill_row)


@router.patch("/{skill_id}/disable")
async def disable_skill(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    skill_row = await _get_skill_or_404(skill_id, db)
    if skill_row.enabled:
        unload_skill(skill_row.name)
        skill_row.enabled = False
        await db.commit()
        await db.refresh(skill_row)
    return _skill_dict(skill_row)


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    skill_row = await _get_skill_or_404(skill_id, db)
    unload_skill(skill_row.name)

    # Remove files from disk
    skill_dir = Path(skill_row.package_path) if skill_row.package_path else SKILLS_STORE / skill_row.name
    if skill_dir.exists():
        shutil.rmtree(skill_dir, ignore_errors=True)

    await db.delete(skill_row)
    await db.commit()


async def _get_skill_or_404(skill_id: int, db: AsyncSession) -> Skill:
    result = await db.execute(select(Skill).where(Skill.id == skill_id))
    skill_row = result.scalar_one_or_none()
    if skill_row is None:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill_row
