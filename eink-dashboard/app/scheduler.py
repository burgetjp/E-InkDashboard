from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.cache import DashboardCache, cache as _default_cache
from app.icons import load_all_icons
from app.quotes import fetch_quote
from app.render_almanac import render_almanac, render_almanac_sam
from app.render_joe import render_joe
from app.render_sam import render_sam
from app.weather import fetch_weather

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def refresh_dashboard(
    cache: DashboardCache = _default_cache,
    noaa_grid: str = "PSR/166,61",
) -> None:
    icons = load_all_icons(size=120)

    weather = None
    noaa_ok = False
    try:
        weather = await fetch_weather(noaa_grid)
        noaa_ok = True
    except Exception as exc:
        logger.warning("NOAA fetch failed: %s", exc)

    quote = None
    quotes_ok = False
    try:
        quote = await fetch_quote()
        quotes_ok = True
    except Exception as exc:
        logger.warning("ZenQuotes fetch failed: %s", exc)

    if weather is None or quote is None:
        cache.noaa_ok = noaa_ok
        cache.quotes_ok = quotes_ok
        return

    joe_png = render_joe(weather, quote, icons)
    sam_png = render_sam(weather, quote, icons)
    cache.store(joe_png, sam_png, noaa_ok=noaa_ok, quotes_ok=quotes_ok)

    cache.store_almanac(
        classic=render_almanac(weather, quote, icons, variant="classic", inverted=False),
        classic_inv=render_almanac(weather, quote, icons, variant="classic", inverted=True),
        modern=render_almanac(weather, quote, icons, variant="modern", inverted=False),
        modern_inv=render_almanac(weather, quote, icons, variant="modern", inverted=True),
    )
    cache.store_almanac_sam(
        render_almanac_sam(weather, quote, icons)
    )


def start_scheduler(noaa_grid: str = "PSR/166,61") -> None:
    scheduler.add_job(
        refresh_dashboard,
        CronTrigger(minute=20),
        kwargs={"noaa_grid": noaa_grid},
        id="refresh_dashboard",
        replace_existing=True,
    )
    scheduler.start()
