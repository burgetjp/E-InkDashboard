from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import Response

from app.cache import cache

proto_router = APIRouter()


@proto_router.get("/almanac-classic.png")
async def almanac_classic() -> Response:
    return Response(content=cache.get_almanac("classic"), media_type="image/png")


@proto_router.get("/almanac-classic-inv.png")
async def almanac_classic_inv() -> Response:
    return Response(content=cache.get_almanac("classic-inv"), media_type="image/png")


@proto_router.get("/almanac-modern.png")
async def almanac_modern() -> Response:
    return Response(content=cache.get_almanac("modern"), media_type="image/png")


@proto_router.get("/almanac-modern-inv.png")
async def almanac_modern_inv() -> Response:
    return Response(content=cache.get_almanac("modern-inv"), media_type="image/png")


@proto_router.get("/almanac-sam.png")
async def almanac_sam() -> Response:
    return Response(content=cache.get_almanac_sam(), media_type="image/png")
