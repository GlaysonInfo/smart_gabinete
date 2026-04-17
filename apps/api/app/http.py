from __future__ import annotations

import math
import uuid
from typing import Any

from fastapi import Request

from .auth import iso_now


def request_id(request: Request) -> str:
    return getattr(request.state, "request_id", str(uuid.uuid4()))


def meta(request: Request) -> dict[str, Any]:
    return {"request_id": request_id(request), "timestamp": iso_now()}


def success(request: Request, data: Any) -> dict[str, Any]:
    return {"data": data, "meta": meta(request)}


def paginated(request: Request, data: list[dict[str, Any]], page: int, page_size: int, total: int) -> dict[str, Any]:
    total_pages = max(1, math.ceil(total / page_size)) if total else 1
    payload = meta(request)
    payload.update({"page": page, "page_size": page_size, "total": total, "total_pages": total_pages})
    return {"data": data, "meta": payload}


def error_payload(request: Request, code: str, message: str, details: Any = None) -> dict[str, Any]:
    return {
        "error": {"code": code, "message": message, "details": details or []},
        "meta": meta(request),
    }

