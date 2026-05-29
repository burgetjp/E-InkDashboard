from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

import httpx

QuoteSource = Literal["primary", "fallback", "cached"]


@dataclass
class QuoteData:
    text: str
    author: str
    source: QuoteSource = "primary"


_FALLBACK_URL = "https://motivational-spark-api.vercel.app/api/quotes/random"
_last_good_quote: Optional[QuoteData] = None


async def fetch_quote() -> QuoteData:
    global _last_good_quote

    # Tier 1: ZenQuotes
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("https://zenquotes.io/api/random")
            resp.raise_for_status()
            data = resp.json()[0]
        result = QuoteData(text=data["q"], author=data["a"], source="primary")
        _last_good_quote = result
        return result
    except Exception:
        pass

    # Tier 2: Motivational Spark
    last_exc: Optional[Exception] = None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(_FALLBACK_URL)
            resp.raise_for_status()
            data = resp.json()
        result = QuoteData(text=data["quote"], author=data["author"], source="fallback")
        _last_good_quote = result
        return result
    except Exception as exc:
        last_exc = exc

    # Tier 3: last cached quote
    if _last_good_quote is not None:
        return QuoteData(
            text=_last_good_quote.text,
            author=_last_good_quote.author,
            source="cached",
        )

    # All tiers exhausted
    raise last_exc  # type: ignore[misc]
