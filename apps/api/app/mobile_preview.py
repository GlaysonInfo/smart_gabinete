from __future__ import annotations

import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .http import error_payload
from .routes import router


app = FastAPI(title=f"{settings.app_name} MOBILE", version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request.state.request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
    response = await call_next(request)
    response.headers["X-Request-Id"] = request.state.request_id
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    code_map = {
        400: "VALIDATION_ERROR",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "BUSINESS_RULE_ERROR",
    }
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(request, code_map.get(exc.status_code, "ERROR"), str(exc.detail)),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content=error_payload(request, "VALIDATION_ERROR", "Campos invalidos no payload.", exc.errors()),
    )


@app.get("/health", tags=["Sistema"])
def health():
    return {"status": "ok", "app": f"{settings.app_name} MOBILE"}


app.include_router(router, prefix=settings.api_prefix)

mobile_dir = settings.root_dir / "apps" / "mobile"
if mobile_dir.exists():
    app.mount("/mobile", StaticFiles(directory=str(mobile_dir), html=True), name="mobile")

mandato_dir = settings.root_dir / "apps" / "mobile_mandato"
if mandato_dir.exists():
    app.mount("/mandato", StaticFiles(directory=str(mandato_dir), html=True), name="mandato")

images_dir = settings.root_dir / "imagens"
if images_dir.exists():
    app.mount("/imagens", StaticFiles(directory=str(images_dir)), name="images")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/mobile/")