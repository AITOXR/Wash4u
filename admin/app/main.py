from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.deps import RedirectToLogin
from app.routers import auth, blog, crm, dashboard, leads, media, orders, pages, products, public_api, settings as settings_router, users

app = FastAPI(title="Wash4You Admin")

# CORS: locked to the public site's own origin — the public API is called
# cross-origin from the static site, everything else (/admin/*) is
# same-origin browser navigation and needs no CORS at all.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.public_site_origin],
    allow_methods=["POST"],
    allow_headers=["Content-Type"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

for router in (auth.router, dashboard.router, pages.router, products.router, blog.router,
               orders.router, crm.router, leads.router, settings_router.router, media.router,
               users.router, public_api.router):
    app.include_router(router)


@app.exception_handler(RedirectToLogin)
async def _redirect_to_login(request: Request, exc: RedirectToLogin):
    return RedirectResponse(f"/admin/login?next={exc.next_path}", status_code=303)


@app.exception_handler(HTTPException)
async def _http_exception_handler(request: Request, exc: HTTPException):
    # Admin API routes (require_api_user) always get JSON, matching the
    # acceptance test "hitting an admin API directly returns 401" —
    # never a redirect, never a leaked traceback.
    if request.url.path.startswith("/api/") or "application/json" in request.headers.get("accept", ""):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    return PlainTextResponse(exc.detail, status_code=exc.status_code)


@app.get("/")
def root():
    return RedirectResponse("/admin", status_code=303)


@app.get("/healthz")
def healthz():
    return {"ok": True}
