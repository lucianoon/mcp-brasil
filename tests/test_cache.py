import time

from mcp_dados_br.cache import TTLCache


def test_guarda_e_recupera_valor() -> None:
    cache: TTLCache = TTLCache()
    cache.set("chave", {"dados": [1, 2]})
    assert cache.get("chave") == {"dados": [1, 2]}


def test_chave_inexistente_retorna_none() -> None:
    cache: TTLCache = TTLCache()
    assert cache.get("nao-existe") is None


def test_expira_apos_ttl(monkeypatch: object) -> None:
    import mcp_dados_br.cache as modulo

    cache: TTLCache = TTLCache(ttl_seconds=10.0)
    agora = time.monotonic()
    monkeypatch.setattr(modulo.time, "monotonic", lambda: agora)
    cache.set("x", 1)

    monkeypatch.setattr(modulo.time, "monotonic", lambda: agora + 11.0)
    assert cache.get("x") is None


def test_limite_de_tamanho_descarta_mais_antigo() -> None:
    cache: TTLCache = TTLCache(max_size=2)
    cache.set("a", 1)
    time.sleep(0.001)
    cache.set("b", 2)
    time.sleep(0.001)
    cache.set("c", 3)
    assert cache.get("a") is None
    assert cache.get("c") == 3
