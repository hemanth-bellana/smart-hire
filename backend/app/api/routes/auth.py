from fastapi import APIRouter, Depends, HTTPException
from fastapi import APIRouter
from app.api.deps import get_current_user, get_db
from sqlalchemy.orm import Session
from app.services.auth_service import (
    authenticate_user,
    create_user_token,
    register_user,
)
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenResponse,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

@router.post("/register")
def register(
    user_data: RegisterRequest,
    db: Session = Depends(get_db),
):
    user = register_user(
        db=db,
        email=user_data.email,
        password=user_data.password,
        full_name=user_data.full_name,
    )

    return {
        "message": "User registered successfully",
        "user": {
            "email": user.email,
            "full_name": user.full_name,
        },
    }


@router.post("/login", response_model=TokenResponse)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    user = authenticate_user(
        db=db,
        email=login_data.email,
        password=login_data.password,
    )

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
        )

    access_token = create_user_token(user.email)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
    )
@router.get("/me")
def get_me(current_user: str = Depends(get_current_user)):
    return {
        "email": current_user,
    }