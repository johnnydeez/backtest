import uuid
from datetime import datetime, timezone
from sqlalchemy import String, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base

class BacktestJob(Base):
    __tablename__ = "backtest_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    status: Mapped[str] = mapped_column(String, default="pending")
    params: Mapped[dict] = mapped_column(JSON)
    result_summary: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    result_file_path: Mapped[str | None] = mapped_column(String, nullable=True)
    charts_path: Mapped[str | None] = mapped_column(String, nullable=True)
    error: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
