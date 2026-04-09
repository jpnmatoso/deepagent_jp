from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx

router = APIRouter(prefix="/auth", tags=["auth"])

JP_BDC_URL = "http://host.docker.internal:8100"


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(request: LoginRequest):
    """Proxy de login para JP BDC API"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{JP_BDC_URL}/auth/login",
                json={
                    "username": request.username,
                    "password": request.password,
                },
                timeout=30.0,
            )

            if response.status_code != 200:
                try:
                    error = response.json()
                except Exception:
                    error = {}
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error.get("detail", "Login failed"),
                )

            return response.json()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail="JP BDC API is not available",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Login error: {str(e)}",
        )
