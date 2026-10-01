from datetime import datetime

from pydantic import BaseModel, ConfigDict


class JobCreate(BaseModel):
    title: str
    description: str
    location: str | None = None
    employment_type: str | None = None


class JobResponse(BaseModel):
    id: int
    title: str
    description: str
    location: str | None
    employment_type: str | None
    created_by: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)