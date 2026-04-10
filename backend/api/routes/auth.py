from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt, JWTError
import bcrypt
import asyncpg
import os

router = APIRouter(prefix="/auth", tags=["auth"])

SECRET = os.getenv("JWT_SECRET")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "60"))


def get_db_url():
    return os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URI")


def create_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET, algorithm=ALGORITHM)


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(request: LoginRequest):
    db_url = get_db_url()
    if not db_url:
        raise HTTPException(500, "Database URL not configured")

    pool = await asyncpg.create_pool(dsn=db_url)
    try:
        async with pool.acquire() as conn:
            user = await conn.fetchrow(
                "SELECT id, username, password_hash FROM users WHERE username = $1 AND status = 'active'",
                request.username,
            )

            if not user:
                raise HTTPException(401, "Invalid credentials")

            if not bcrypt.checkpw(
                request.password.encode("utf-8"), user["password_hash"].encode("utf-8")
            ):
                raise HTTPException(401, "Invalid credentials")

            token = create_token({"sub": user["username"], "user_id": user["id"]})

            return {
                "token": token,
                "expires_at": (
                    datetime.utcnow() + timedelta(minutes=EXPIRE_MINUTES)
                ).isoformat(),
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Login error: {str(e)}")
    finally:
        await pool.close()
