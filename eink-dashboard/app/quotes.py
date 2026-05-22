from dataclasses import dataclass

import httpx


@dataclass
class QuoteData:
    text: str
    author: str


async def fetch_quote() -> QuoteData:
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get("https://zenquotes.io/api/random")
        resp.raise_for_status()
        data = resp.json()[0]
    return QuoteData(text=data["q"], author=data["a"])
