from datetime import datetime, timedelta
from typing import Optional, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from core.config import settings
from models.database import User, get_db
from core.logging import logger

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 bearer token settings
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

# JWT secret key and algorithm
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = "HS256"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash.

    Args:
        plain_password (str): Plain text password
        hashed_password (str): Hashed password

    Returns:
        bool: True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a password.

    Args:
        password (str): Plain text password

    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def authenticate_user(db: Session, email: str, password: str) -> Union[User, bool]:
    """
    Authenticate a user by email and password.

    Args:
        db (Session): Database session
        email (str): User email
        password (str): User password

    Returns:
        Union[User, bool]: User object if authenticated, False otherwise
    """
    # Try to find by email
    user = db.query(User).filter(User.email == email).first()

    # If not found by email, try username
    if not user:
        user = db.query(User).filter(User.username == email).first()

    if not user:
        return False

    if not verify_password(password, user.hashed_password):
        return False

    return user


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data (dict): Token payload data
        expires_delta (Optional[timedelta]): Token expiration time

    Returns:
        str: JWT token
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: Session = Depends(get_db)
) -> User:
    """
    Get the current user from a JWT token.

    Args:
        token (str): JWT token
        db (Session): Database session

    Returns:
        User: User object

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: int = payload.get("user_id")

        if email is None or user_id is None:
            logger.warning("Invalid token payload")
            raise credentials_exception

    except JWTError as e:
        logger.error(f"JWT Error: {str(e)}")
        raise credentials_exception

    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        logger.warning(f"User not found: ID {user_id}")
        raise credentials_exception

    if not user.is_active:
        logger.warning(f"Inactive user: ID {user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user