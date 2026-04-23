from __future__ import annotations

import uuid

import yaml
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .config import settings
from .http import error_payload
from .routes import router


app = FastAPI(title=settings.app_name, version="1.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_origin_regex=settings.cors_allow_origin_regex,
    allow_credentials=False,
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
    return {"status": "ok", "app": settings.app_name}


app.include_router(router, prefix=settings.api_prefix)

web_dir = settings.root_dir / "apps" / "web"
if web_dir.exists():
    app.mount("/app", StaticFiles(directory=str(web_dir), html=True), name="web")

mobile_dir = settings.root_dir / "apps" / "mobile"
if mobile_dir.exists():
    app.mount("/mobile", StaticFiles(directory=str(mobile_dir), html=True), name="mobile")

mandato_dir = settings.root_dir / "apps" / "mobile_mandato"
if mandato_dir.exists():
    app.mount("/mandato", StaticFiles(directory=str(mandato_dir), html=True), name="mandato")

images_dir = settings.root_dir / "imagens"
if images_dir.exists():
    app.mount("/imagens", StaticFiles(directory=str(images_dir)), name="images")

settings.upload_dir.mkdir(parents=True, exist_ok=True)
if settings.upload_dir.exists():
    app.mount("/uploads-public", StaticFiles(directory=str(settings.upload_dir)), name="uploads-public")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/app/")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_path = settings.root_dir / "openapi_refinado_gabinete_ia_impl_ready.yaml"
    if openapi_path.exists():
        with openapi_path.open("r", encoding="utf-8") as fp:
            app.openapi_schema = yaml.safe_load(fp)
        return app.openapi_schema
    return app.openapi()


app.openapi = custom_openapi

