import pytest
import respx
import httpx

from app.quotes import fetch_quote, QuoteData


@respx.mock
async def test_fetch_quote_success():
    respx.get("https://zenquotes.io/api/random").mock(
        return_value=httpx.Response(
            200,
            json=[{"q": "The divine is not something high above us.", "a": "Morihei Ueshiba"}],
        )
    )
    result = await fetch_quote()
    assert isinstance(result, QuoteData)
    assert result.text == "The divine is not something high above us."
    assert result.author == "Morihei Ueshiba"


@respx.mock
async def test_fetch_quote_http_error():
    respx.get("https://zenquotes.io/api/random").mock(
        return_value=httpx.Response(429)
    )
    with pytest.raises(httpx.HTTPStatusError):
        await fetch_quote()
