
import httpx
import pytest
import respx

from mcp_brasil.tools import bcb

PTAX_URL = (
    "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/"
    "CotacaoMoedaPeriodo(moeda=@moeda,dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)"
)

RESPOSTA_PTAX = {
    "value": [
        {
            "cotacaoCompra": 5.0,
            "cotacaoVenda": 5.1,
            "dataHoraCotacao": "2026-08-18 10:00:00.000",
            "tipoBoletim": "Abertura",
        },
        {
            "cotacaoCompra": 5.2,
            "cotacaoVenda": 5.3,
            "dataHoraCotacao": "2026-08-19 13:00:00.000",
            "tipoBoletim": "Fechamento",
        },
        {
            "cotacaoCompra": 5.4,
            "cotacaoVenda": 5.5,
            "dataHoraCotacao": "2026-08-20 13:00:00.000",
            "tipoBoletim": "Fechamento",
        },
    ]
}


def test_conversao_datas() -> None:
    assert bcb._data_sgs("2026-08-24") == "24/08/2026"
    assert bcb._data_ptax("2026-08-24") == "08-24-2026"


@respx.mock
async def test_bcb_serie_formata_registros() -> None:
    respx.get(
        "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados"
    ).mock(
        return_value=httpx.Response(
            200,
            json=[
                {"data": "01/06/2026", "valor": "0.24"},
                {"data": "01/07/2026", "valor": "0.17"},
            ],
        )
    )
    saida = await bcb.bcb_serie(433, "2026-06-01", "2026-07-31")
    assert "Série 433:" in saida
    assert "01/06/2026: 0.24" in saida
    assert "01/07/2026: 0.17" in saida


async def test_bcb_serie_periodo_invalido() -> None:
    with pytest.raises(ValueError, match="anterior"):
        await bcb.bcb_serie(433, "2026-07-01", "2026-06-01")


@respx.mock
async def test_bcb_cambio_resume_apenas_fechamento() -> None:
    route = respx.get(PTAX_URL).mock(
        return_value=httpx.Response(200, json=RESPOSTA_PTAX)
    )
    saida = await bcb.bcb_cambio("USD", dias=2)
    requisicao = route.calls.last.request.url.params
    assert requisicao["@moeda"] == "'USD'"
    assert requisicao["@dataInicial"].startswith("'")
    assert requisicao["$format"] == "json"
    assert "compra mín. R$ 5.2" in saida
    assert "média R$ 5.3000" in saida
    assert "Abertura" not in saida


@respx.mock
async def test_bcb_cambio_moeda_inexistente() -> None:
    respx.get(PTAX_URL).mock(return_value=httpx.Response(200, json={"value": []}))
    saida = await bcb.bcb_cambio("XXX")
    assert "Nenhuma cotação encontrada" in saida


@respx.mock
async def test_bcb_moedas_lista_simbolos() -> None:
    respx.get(
        "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata/Moedas"
    ).mock(
        return_value=httpx.Response(
            200,
            json={"value": [{"simbolo": "EUR", "nomeFormatado": "Euro"}]},
        )
    )
    saida = await bcb.bcb_moedas()
    assert "EUR — Euro" in saida
