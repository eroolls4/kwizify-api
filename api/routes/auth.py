from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from models.database import get_db, User
from core.logging import logger
from services.auth_service import (
    authenticate_user,
    create_access_token,
    get_password_hash,
    get_current_user
)
from schemas.auth import UserCreate, Token, UserResponse

router = APIRouter()

# OAuth2 bearer token setup
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# Access token expiration time (minutes)
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


@router.post("/signup", response_model=UserResponse)
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.

    Args:
        user (UserCreate): User signup data
        db (Session): Database session

    Returns:
        UserResponse: Created user data
    """
    logger.info(f"Signup attempt for username: {user.username}")

    # Check if username already exists
    db_user = db.query(User).filter(User.username == user.username).first()
    if db_user:
        logger.warning(f"Signup failed: Username {user.username} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # Check if email already exists
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        logger.warning(f"Signup failed: Email {user.email} already exists")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Create new user with hashed password
    hashed_password = get_password_hash(user.password)
    new_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        is_active=True
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"User created successfully: {user.username}")

        return {
            "id": new_user.id,
            "username": new_user.username,
            "email": new_user.email,
            "is_active": new_user.is_active
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate a user and return an access token.

    Args:
        form_data (OAuth2PasswordRequestForm): Login credentials
        db (Session): Database session

    Returns:
        Token: Access token and token type
    """
    logger.info(f"Login attempt for username: {form_data.username}")

    # Authenticate user (using email as username)
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        logger.warning(f"Login failed: Invalid credentials for {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": user.id},
        expires_delta=access_token_expires
    )

    logger.info(f"Login successful for user: {user.username}")
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_active": user.is_active
        }
    }


@router.get("/me", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get the current authenticated user's profile.

    Args:
        current_user (User): Current authenticated user

    Returns:
        UserResponse: User profile data
    """
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_active": current_user.is_active
    }