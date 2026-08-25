import httpx
import pytest
import respx

from mcp_dados_br.http import ApiError, cache_key, get_json


@respx.mock
async def test_get_json_sucesso() -> None:
    route = respx.get("https://api.exemplo.test/dados").mock(
        return_value=httpx.Response(200, json={"ok": True})
    )
    resultado = await get_json("https://api.exemplo.test/dados")
    assert resultado == {"ok": True}
    assert route.called


@respx.mock
async def test_get_json_usa_cache_na_segunda_chamada() -> None:
    route = respx.get("https://api.exemplo.test/dados").mock(
        return_value=httpx.Response(200, json={"n": 42})
    )
    primeiro = await get_json("https://api.exemplo.test/dados")
    segundo = await get_json("https://api.exemplo.test/dados")
    assert route.call_count == 1
    assert primeiro == segundo


@respx.mock
async def test_get_json_erro_4xx_levanta_apierror() -> None:
    respx.get("https://api.exemplo.test/erro").mock(
        return_value=httpx.Response(400, json={"erro": "requisição inválida"})
    )
    with pytest.raises(ApiError, match="HTTP 400"):
        await get_json("https://api.exemplo.test/erro")


@respx.mock
async def test_get_json_resposta_nao_json_levanta_apierror() -> None:
    respx.get("https://api.exemplo.test/html").mock(
        return_value=httpx.Response(200, text="<html>ops</html>")
    )
    with pytest.raises(ApiError, match="não-JSON"):
        await get_json("https://api.exemplo.test/html")


@respx.mock
async def test_get_json_tenta_novamente_apos_erro_de_rede() -> None:
    route = respx.get("https://api.exemplo.test/flaky").mock(
        side_effect=[
            httpx.ConnectTimeout("timeout"),
            httpx.Response(200, json={"tentativa": 2}),
        ]
    )
    resultado = await get_json("https://api.exemplo.test/flaky")
    assert resultado == {"tentativa": 2}
    assert route.call_count == 2


@respx.mock
async def test_get_json_esgota_tentativas() -> None:
    route = respx.get("https://api.exemplo.test/offline").mock(
        side_effect=httpx.ConnectError("sem conexão")
    )
    with pytest.raises(ApiError, match="Falha ao consultar"):
        await get_json("https://api.exemplo.test/offline")
    assert route.call_count == 2


def test_cache_key_com_params_ordenados() -> None:
    chave = cache_key("https://x.test/api", {"b": "2", "a": "1"})
    assert chave == "https://x.test/api?a=1&b=2"


def test_cache_key_ignora_parametros_none() -> None:
    chave = cache_key("https://x.test/api", {"a": "1", "vazio": None})
    assert chave == "https://x.test/api?a=1"
