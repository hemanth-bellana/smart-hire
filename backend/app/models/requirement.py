from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class JobRequirement(Base):
    __tablename__ = "job_requirements"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id"),
        nullable=False,
        index=True,
    )

    required_skills: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    preferred_skills: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    minimum_experience_years: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    education: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    other_requirements: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )