from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.auth import router as auth_router
from app.core.config import settings

from app.api.routes.jobs import router as jobs_router

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered HR recruitment and resume screening API",
    version="1.0.0",
)

app.include_router(auth_router)
app.include_router(health_router)
app.include_router(jobs_router)


@app.get("/")
def root():
    return {
        "message": "SmartHire API is running",
        "status": "success",
    }