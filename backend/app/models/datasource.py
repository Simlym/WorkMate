from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Datasource(Base):
    __tablename__ = "datasources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String(32), nullable=False)  # mysql/postgresql/mssql/http_api/shared
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)  # connection params
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
