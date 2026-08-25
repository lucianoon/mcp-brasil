import pytest

from mcp_dados_br.http import reset_cache


@pytest.fixture(autouse=True)
def _cache_limpo_por_teste() -> None:
    reset_cache()
    yield
    reset_cache()
