from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    version: Mapped[str] = mapped_column(String(32), nullable=False, default="0.1.0")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    package_path: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    entry_point: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    installed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
