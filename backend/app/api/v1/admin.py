"""Admin API — user management. Requires is_admin=True."""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.core.deps import get_current_user
from app.core.security import hash_password
from app.models.user import User

router = APIRouter()


def _require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def _user_dict(u: User) -> dict:
    return {
        "id": u.id,
        "employee_id": u.employee_id,
        "display_name": u.display_name,
        "is_active": u.is_active,
        "is_admin": u.is_admin,
        "created_at": u.created_at.isoformat(),
    }


class UserCreate(BaseModel):
    employee_id: str
    display_name: str = ""
    password: str
    is_admin: bool = False


class UserUpdate(BaseModel):
    display_name: str | None = None
    is_active: bool | None = None
    is_admin: bool | None = None
    password: str | None = None


@router.get("/users")
async def list_users(
    _admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).order_by(User.employee_id))
    return [_user_dict(u) for u in result.scalars().all()]


@router.post("/users", status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    _admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(User).where(User.employee_id == body.employee_id))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Employee ID already exists")

    user = User(
        employee_id=body.employee_id,
        display_name=body.display_name or body.employee_id,
        password_hash=hash_password(body.password),
        is_active=True,
        is_admin=body.is_admin,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _user_dict(user)


@router.patch("/users/{user_id}")
async def update_user(
    user_id: int,
    body: UserUpdate,
    _admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user_or_404(user_id, db)
    updates = body.model_dump(exclude_none=True)
    if "password" in updates:
        user.password_hash = hash_password(updates.pop("password"))
    for field, value in updates.items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return _user_dict(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    admin: User = Depends(_require_admin),
    db: AsyncSession = Depends(get_db),
):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    user = await _get_user_or_404(user_id, db)
    await db.delete(user)
    await db.commit()


async def _get_user_or_404(user_id: int, db: AsyncSession) -> User:
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user
