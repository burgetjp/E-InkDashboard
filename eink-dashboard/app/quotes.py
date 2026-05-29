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


async def fetch_quote() -> QuoteData:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get("https://zenquotes.io/api/random")
        resp.raise_for_status()
        data = resp.json()[0]
    return QuoteData(text=data["q"], author=data["a"])
