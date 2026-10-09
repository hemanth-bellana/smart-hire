from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ScreeningRequirement(Base):
    __tablename__ = "screening_requirements"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    screening_id: Mapped[int] = mapped_column(
        ForeignKey("screenings.id"),
        nullable=False,
        unique=True,
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

    maximum_experience_years: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    experience_requirement_type: Mapped[str] = mapped_column(
        String(50),
        default="NONE",
        nullable=False,
    )

    required_experience_areas: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    education: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )