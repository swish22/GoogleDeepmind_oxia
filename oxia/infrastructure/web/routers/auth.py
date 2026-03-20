from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException

from auth import create_token, hash_password, verify_password
from models import AuthLoginRequest, AuthRegisterRequest, TokenResponse
from oxia.infrastructure.web.deps import ContainerDep

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(req: AuthRegisterRequest, container: ContainerDep) -> TokenResponse:
    username = (req.username or "").strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username is required.")
    if container.user_persistence.get_user_by_username(username) is not None:
        raise HTTPException(status_code=409, detail="Username already exists.")
    user_id = uuid.uuid4().hex
    container.user_persistence.store_user(
        user_id=user_id,
        username=username,
        password_hash=hash_password(req.password),
    )
    token = create_token(user_id=user_id, username=username)
    return TokenResponse(access_token=token)


@router.post("/login", response_model=TokenResponse)
def login(req: AuthLoginRequest, container: ContainerDep) -> TokenResponse:
    username = (req.username or "").strip()
    if not username:
        raise HTTPException(status_code=400, detail="Username is required.")
    user = container.user_persistence.get_user_by_username(username)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    if not verify_password(req.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    token = create_token(user_id=user["id"], username=user["username"])
    return TokenResponse(access_token=token)
