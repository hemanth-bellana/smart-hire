from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    job_id: Mapped[int] = mapped_column(
        ForeignKey("jobs.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    resume_text: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    skills: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    education: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    experience_years: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    previous_companies: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    certifications: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    extracted_metadata: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    match_score: Mapped[float | None] = mapped_column(
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="PENDING",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )