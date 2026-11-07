
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class CandidateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    screening_id: int | None
    name: str | None
    email: str | None
    phone: str | None
    location: str | None
    skills: str | None
    education: str | None
    experience_years: int | None
    previous_companies: str | None
    certifications: str | None
    match_score: float | None
    status: str
    created_at: datetime
