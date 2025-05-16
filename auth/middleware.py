from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
from sqlalchemy.future import select
from auth.utils import ALGORITHM, SECRET_KEY
from models.database import AsyncSessionLocal
from models.database import User


async def jwt_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        response = JSONResponse(content={"message": "Preflight OK"}, status_code=200)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        return response

    path = request.url.path

    if not path.startswith("/api"):
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        return response

    authorization = request.headers.get("Authorization")
    if not authorization:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Authorization header missing"},
            headers={"WWW-Authenticate": "Bearer", "Access-Control-Allow-Origin": "*"},
        )

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer":
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid authentication scheme"},
            headers={"WWW-Authenticate": "Bearer", "Access-Control-Allow-Origin": "*"},
        )

    if not token:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Token missing"},
            headers={"WWW-Authenticate": "Bearer", "Access-Control-Allow-Origin": "*"},
        )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token payload"},
                headers={"WWW-Authenticate": "Bearer", "Access-Control-Allow-Origin": "*"},
            )

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User).where(User.username == username))
            user = result.scalars().first()

            if not user:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "User not found"},
                    headers={"WWW-Authenticate": "Bearer", "Access-Control-Allow-Origin": "*"},
                )

            request.state.user = user

    except JWTError:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "Invalid token"},
            headers={"WWW-Authenticate": "Bearer", "Access-Control-Allow-Origin": "*"},
        )

    # Continue processing the request
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
    return response
