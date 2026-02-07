from fastapi import APIRouter, HTTPException, Depends, Header, status
from app.models.schemas import UserRegister, UserLogin, TokenResponse, UserResponse, UpdateNameRequest
from app.services.auth_service import AuthService
from app.utils.security import create_access_token, decode_access_token
from app.models.database_init import get_db
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/register", response_model=TokenResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    success, message = AuthService.register_user(user_data, db)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )

    # Create access token
    access_token = create_access_token(
        data={"sub": user_data.email},
        expires_delta=timedelta(minutes=30)
    )

    user = UserResponse(email=user_data.email, name=user_data.name)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user
    )

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Login user with email and password"""
    success, user = AuthService.authenticate_user(credentials.email, credentials.password, db)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # Create access token
    access_token = create_access_token(
        data={"sub": credentials.email},
        expires_delta=timedelta(minutes=30)
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user
    )

@router.get("/me", response_model=UserResponse)
async def get_me(token: str = None, db: Session = Depends(get_db)):
    """Get current user info from token"""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token not provided"
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    email = payload.get("sub")
    user = AuthService.get_user(email, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user

@router.put("/update-name", response_model=UserResponse)
async def update_name(
    body: UpdateNameRequest,
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Update user name"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header required"
        )

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found in token"
        )

    if not body.name or not body.name.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name cannot be empty"
        )

    success, user = AuthService.update_name(email, body.name.strip(), db)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user
