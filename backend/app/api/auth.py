"""Auth endpoints — demo login issuing JWTs."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from ..core.security import DEMO_USERS, create_access_token
from ..schemas import LoginRequest, TokenOut

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
async def login(body: LoginRequest):
    user = DEMO_USERS.get(body.username)
    if not user or user["password"] != body.password:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")
    token = create_access_token(body.username, user["role"])
    return TokenOut(access_token=token, role=user["role"], username=body.username)
