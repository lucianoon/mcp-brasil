from datetime import date, timedelta

import httpx
import pytest
import respx

from mcp_dados_br.tools import inmet

ESTACOES = [
    {
        "CD_ESTACAO": "A001",
        "DC_NOME": "BRASILIA",
        "SG_ESTADO": "DF",
        "FL_CAPITAL": "S",
        "VL_ALTITUDE": "1172",
        "CD_SITUACAO": "Operante",
    },
    {
        "CD_ESTACAO": "A002",
        "DC_NOME": "AGUA BRANCA",
        "SG_ESTADO": "AL",
        "FL_CAPITAL": "N",
        "VL_ALTITUDE": "450",
        "CD_SITUACAO": "Desativada",
    },
]


async def test_tipo_invalido() -> None:
    with pytest.raises(ValueError, match="Tipo desconhecido"):
        await inmet.inmet_estacoes("X")


@respx.mock
async def test_inmet_estacoes_filtra_desativadas_e_uf() -> None:
    route = respx.get("https://apitempo.inmet.gov.br/estacoes/T").mock(
        return_value=httpx.Response(200, json=ESTACOES)
    )
    saida = await inmet.inmet_estacoes("T", uf="df")
    assert "1 estações automáticas:" in saida
    assert "A001 — BRASILIA (DF [capital], 1172 m)" in saida
    assert "Desativada" not in saida and "A002" not in saida
    assert route.called


@respx.mock
async def test_inmet_estacoes_uf_sem_estacoes() -> None:
    respx.get("https://apitempo.inmet.gov.br/estacoes/M").mock(
        return_value=httpx.Response(200, json=[])
    )
    saida = await inmet.inmet_estacoes("convencionais", uf="RR")
    assert "Nenhuma estação convencionais" in saida


async def test_inmet_dados_sem_token_orienta_usuario(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("INMET_TOKEN", raising=False)
    saida = await inmet.inmet_dados("A001")
    assert "INMET_TOKEN" in saida
    assert "portal.inmet.gov.br" in saida


@respx.mock
async def test_inmet_dados_com_token_formata_registros(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INMET_TOKEN", "segredo")
    hoje = date.today()
    ontem = hoje - timedelta(days=1)
    respx.get(
        f"https://apitempo.inmet.gov.br/token/estacao/{ontem}/{hoje}/A001/segredo"
    ).mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "DT_MEDICAO": "2026-08-24",
                    "HR_MEDICAO": 1200,
                    "TEM_INS": 27.6,
                    "UMD_INS": 35,
                    "VEN_VEL": None,
                    "PRE_INS": 1013.2,
                }
            ],
        )
    )
    saida = await inmet.inmet_dados("a001", dias=1)
    assert "temp °C 27.6" in saida
    assert "ur % 35" in saida
    assert "vento m/s" not in saida
    assert "12:00 UTC" in saida
