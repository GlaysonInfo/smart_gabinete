from __future__ import annotations

from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .auth import decode_token
from .config import settings
from .store import JsonStore


store = JsonStore(settings.db_file)
bearer_scheme = HTTPBearer(auto_error=False)


def get_store() -> JsonStore:
    return store


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    repo: JsonStore = Depends(get_store),
) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credencial ausente.",
        )
    payload = decode_token(credentials.credentials)
    user = repo.get("usuarios", payload["sub"])
    if not user or not user.get("ativo", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario inativo ou inexistente.",
        )
    return user

