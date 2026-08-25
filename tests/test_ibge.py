import httpx
import pytest
import respx

from mcp_brasil.tools import ibge

SIDRA_URL = "https://servicodados.ibge.gov.br/api/v3/agregados/4709/periodos/2022/variaveis/93"

RESPOSTA_SIDRA = [
    {
        "id": "93",
        "variavel": "População residente",
        "unidade": "Pessoas",
        "resultados": [
            {
                "classificacoes": [
                    {"id": "2", "nome": "Sexo", "categoria": {"58": "Total"}}
                ],
                "series": [
                    {
                        "localidade": {"id": "35", "nome": "São Paulo"},
                        "serie": {"2022": "46649132"},
                    }
                ],
            }
        ],
    }
]


@respx.mock
async def test_ibge_populacao_formata_saida() -> None:
    respx.get(SIDRA_URL).mock(return_value=httpx.Response(200, json=RESPOSTA_SIDRA))
    saida = await ibge.ibge_populacao("SP", 2022)
    assert "População residente" in saida
    assert "São Paulo" in saida
    assert "46649132" in saida


@respx.mock
async def test_ibge_populacao_br_usa_nivel_nacional() -> None:
    route = respx.get(
        "https://servicodados.ibge.gov.br/api/v3/agregados/4709/periodos/-1/variaveis/93"
    ).mock(return_value=httpx.Response(200, json=RESPOSTA_SIDRA))
    await ibge.ibge_populacao("BR")
    assert route.calls.last.request.url.params["localidades"] == "N1[1]"


async def test_uf_invalida_levanta_valueerror() -> None:
    with pytest.raises(ValueError, match="UF desconhecida"):
        await ibge.ibge_populacao("XX")


@respx.mock
async def test_ibge_municipios_filtra_por_nome() -> None:
    respx.get("https://servicodados.ibge.gov.br/api/v1/localidades/estados/SP/municipios").mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "id": 3509502,
                    "nome": "Campinas",
                    "microrregiao": {
                        "mesorregiao": {"UF": {"sigla": "SP"}}
                    },
                },
                {
                    "id": 3512706,
                    "nome": "Jundiaí",
                    "microrregiao": {"mesorregiao": {"UF": {"sigla": "SP"}}},
                },
            ],
        )
    )
    saida = await ibge.ibge_municipios("CAMPINAS", "SP")
    assert "3509502 — Campinas — SP" in saida
    assert "Jundiaí" not in saida


@respx.mock
async def test_ibge_sidra_sem_dados() -> None:
    respx.get(
        "https://servicodados.ibge.gov.br/api/v3/agregados/9999/periodos/-1/variaveis/0"
    ).mock(return_value=httpx.Response(200, json=[]))
    saida = await ibge.ibge_sidra("9999", "0")
    assert saida == "Nenhum dado encontrado para os parâmetros informados."
