from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import Response, JSONResponse

from app.cache import cache
from app.config import settings
from app.proto_router import proto_router
from app.scheduler import refresh_dashboard, scheduler, start_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    await refresh_dashboard(cache=cache, noaa_grid=settings.noaa_grid)
    start_scheduler(noaa_grid=settings.noaa_grid)
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="InkyDashboard", lifespan=lifespan)
app.include_router(proto_router, prefix="/proto")


@app.get("/dashboard/joe.png")
async def joe_png() -> Response:
    return Response(content=cache.get_joe(), media_type="image/png")


@app.get("/dashboard/sam.png")
async def sam_png() -> Response:
    return Response(content=cache.get_sam(), media_type="image/png")


@app.post("/admin/refresh")
async def admin_refresh() -> JSONResponse:
    await refresh_dashboard(cache=cache, noaa_grid=settings.noaa_grid)
    return JSONResponse({"refreshed": True, "noaa_ok": cache.noaa_ok, "quotes_ok": cache.quotes_ok})


@app.get("/health")
async def health() -> JSONResponse:
    last = cache.last_refresh.isoformat() if cache.last_refresh else None
    return JSONResponse({
        "last_refresh": last,
        "noaa_ok": cache.noaa_ok,
        "quotes_ok": cache.quotes_ok,
    })
