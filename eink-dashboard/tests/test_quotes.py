import pytest
import respx
import httpx

from app.quotes import fetch_quote, QuoteData

FALLBACK_URL = "https://motivational-spark-api.vercel.app/api/quotes/random"
ZENQUOTES_URL = "https://zenquotes.io/api/random"


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
    """Both APIs fail and no cache → raises HTTPStatusError."""
    import app.quotes as quotes_module
    quotes_module._last_good_quote = None

    respx.get(ZENQUOTES_URL).mock(return_value=httpx.Response(429))
    respx.get(FALLBACK_URL).mock(return_value=httpx.Response(503))
    with pytest.raises(httpx.HTTPStatusError):
        await fetch_quote()


def test_quote_data_default_source_is_primary():
    q = QuoteData(text="Hello", author="World")
    assert q.source == "primary"


def test_quote_data_accepts_fallback_source():
    q = QuoteData(text="Hello", author="World", source="fallback")
    assert q.source == "fallback"


def test_quote_data_accepts_cached_source():
    q = QuoteData(text="Hello", author="World", source="cached")
    assert q.source == "cached"


@respx.mock
async def test_fetch_quote_uses_fallback_on_zenquotes_failure():
    """ZenQuotes 429 → fallback API succeeds → source='fallback'."""
    import app.quotes as quotes_module
    quotes_module._last_good_quote = None  # reset module state

    respx.get(ZENQUOTES_URL).mock(return_value=httpx.Response(429))
    respx.get(FALLBACK_URL).mock(
        return_value=httpx.Response(
            200,
            json={"quote": "Keep going.", "author": "Unknown"},
        )
    )
    result = await quotes_module.fetch_quote()
    assert result.source == "fallback"
    assert result.text == "Keep going."
    assert result.author == "Unknown"


@respx.mock
async def test_fetch_quote_uses_cache_when_both_apis_fail():
    """Both APIs fail → returns last cached quote with source='cached'."""
    import app.quotes as quotes_module
    quotes_module._last_good_quote = QuoteData(
        text="Cached quote", author="Cache Author", source="primary"
    )

    respx.get(ZENQUOTES_URL).mock(return_value=httpx.Response(503))
    respx.get(FALLBACK_URL).mock(return_value=httpx.Response(503))

    result = await quotes_module.fetch_quote()
    assert result.source == "cached"
    assert result.text == "Cached quote"
    assert result.author == "Cache Author"


@respx.mock
async def test_fetch_quote_raises_when_all_fail_and_no_cache():
    """Both APIs fail and no cache → raises."""
    import app.quotes as quotes_module
    quotes_module._last_good_quote = None

    respx.get(ZENQUOTES_URL).mock(return_value=httpx.Response(503))
    respx.get(FALLBACK_URL).mock(return_value=httpx.Response(503))

    with pytest.raises(httpx.HTTPStatusError):
        await quotes_module.fetch_quote()
