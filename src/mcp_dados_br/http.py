import asyncio
import logging
from typing import Any
from urllib.parse import quote

import httpx

from mcp_dados_br.cache import TTLCache

logger = logging.getLogger(__name__)

_USER_AGENT = "mcp-dados-br/0.1 (+https://github.com/lucianoon/mcp-dados-br)"
_TIMEOUT = httpx.Timeout(30.0, connect=5.0)
_RETRYS_DELAY = [0.5, 1.5]

_cache = TTLCache(ttl_seconds=600.0)
_client: httpx.AsyncClient | None = None
_lock = asyncio.Lock()


class ApiError(Exception):
    pass


async def get_client() -> httpx.AsyncClient:
    global _client
    async with _lock:
        if _client is None or _client.is_closed:
            _client = httpx.AsyncClient(
                headers={"User-Agent": _USER_AGENT},
                timeout=_TIMEOUT,
                follow_redirects=True,
            )
        return _client


def reset_cache() -> None:
    _cache.clear()


def cache_key(url: str, params: dict[str, Any] | None) -> str:
    if not params:
        return url
    query = "&".join(f"{k}={v}" for k, v in sorted(params.items()) if v is not None)
    return f"{url}?{query}"


def _query_string(params: dict[str, Any]) -> str:
    return "&".join(
        f"{k}={quote(str(v), safe='')}"
        for k, v in sorted(params.items())
        if v is not None
    )


async def get_json(url: str, params: dict[str, Any] | None = None) -> Any:
    key = cache_key(url, params)
    cached = _cache.get(key)
    if cached is not None:
        return cached

    request_url = f"{url}?{_query_string(params)}" if params else url
    logger.debug("GET %s", request_url)
    client = await get_client()
    last_error: Exception | None = None
    for attempt in range(len(_RETRYS_DELAY) + 1):
        try:
            response = await client.get(request_url)
            if response.status_code >= 400:
                corpo = response.text[:200]
                raise ApiError(f"HTTP {response.status_code} ao consultar {url}: {corpo}")
            try:
                data: Any = response.json()
            except ValueError as exc:
                raise ApiError(f"Resposta não-JSON de {url}: {exc}") from exc
            _cache.set(key, data)
            return data
        except httpx.TransportError as exc:
            last_error = exc
            logger.warning("Tentativa %d falhou para %s: %r", attempt + 1, url, exc)
            if attempt < len(_RETRYS_DELAY):
                await asyncio.sleep(_RETRYS_DELAY[attempt])
    raise ApiError(f"Falha ao consultar {url}: {last_error}") from last_error


async def aclose() -> None:
    global _client
    async with _lock:
        if _client is not None and not _client.is_closed:
            await _client.aclose()
        _client = None
