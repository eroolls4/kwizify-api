from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
from auth.utils import ALGORITHM, SECRET_KEY
from models.database import SessionLocal
from models.database import User


async def jwt_middleware(request: Request, call_next):
    """
    Middleware to check JWT tokens for protected routes.
    Excludes auth endpoints and allows them to proceed without authentication.
    """
    # Exclude auth routes from JWT validation
    if request.url.path.startswith("/auth") or request.url.path == "/":
        return await call_next(request)

    authorization = request.headers.get("Authorization")
    if not authorization:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Authorization header missing"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid authentication scheme"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not token:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Token missing"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token payload"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.username == username).first()
            if not user:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "User not found"},
                    headers={"WWW-Authenticate": "Bearer"},
                )

            request.state.user = user

        finally:
            db.close()

    except JWTError:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid token"},
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Continue processing the request
    return await call_next(request)