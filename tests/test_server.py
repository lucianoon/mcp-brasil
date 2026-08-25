import asyncio

from mcp_dados_br.server import create_server

NOMES_ESPERADOS = {
    "ibge_populacao",
    "ibge_pib",
    "ibge_municipios",
    "ibge_sidra",
    "bcb_serie",
    "bcb_cambio",
    "bcb_moedas",
    "bcb_focus",
    "inmet_estacoes",
    "inmet_dados",
    "camara_deputados",
    "camara_detalhes_deputado",
    "camara_proposicoes",
    "camara_votacoes_proposicao",
    "camara_agenda",
    "camara_tramitacao",
}


def test_servidor_registra_todas_as_tools() -> None:
    async def coletar() -> list[str]:
        servidor = create_server()
        tools = await servidor.list_tools()
        return [t.name for t in tools]

    nomes = set(asyncio.run(coletar()))
    assert nomes == NOMES_ESPERADOS
