import logging
import os
import sys
from collections.abc import Awaitable, Callable

from mcp.server import MCPServer

from mcp_dados_br.tools import bcb, camara, ibge, inmet, senado

_INSTRUCTIONS = """\
Servidor de dados públicos brasileiros. Use as ferramentas para responder
perguntas sobre estatísticas do IBGE (população, PIB), indicadores econômicos
do Banco Central (Selic, IPCA, câmbio PTAX, expectativas do boletim Focus),
estações meteorológicas do INMET, atividade legislativa da Câmara dos
Deputados e do Senado Federal (senadores, matérias e votações). Todas as
respostas são texto em português brasileiro pronto para uso. Prefira sempre
as ferramentas específicas antes da genérica ibge_sidra.
"""


def create_server() -> MCPServer:
    mcp = MCPServer("mcp-dados-br", instructions=_INSTRUCTIONS)
    tools: list[Callable[..., Awaitable[str]]] = [
        ibge.ibge_populacao,
        ibge.ibge_pib,
        ibge.ibge_municipios,
        ibge.ibge_sidra,
        bcb.bcb_serie,
        bcb.bcb_cambio,
        bcb.bcb_moedas,
        bcb.bcb_focus,
        inmet.inmet_estacoes,
        inmet.inmet_dados,
        camara.camara_deputados,
        camara.camara_detalhes_deputado,
        camara.camara_proposicoes,
        camara.camara_votacoes_proposicao,
        camara.camara_agenda,
        camara.camara_tramitacao,
        senado.senado_senadores,
        senado.senado_materias,
        senado.senado_votacoes,
    ]
    for tool in tools:
        mcp.tool()(tool)
    return mcp


def _configurar_logging() -> None:
    nivel = os.environ.get("MCP_LOG_LEVEL", "WARNING").upper()
    logging.basicConfig(
        level=getattr(logging, nivel, logging.WARNING),
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def main() -> None:
    _configurar_logging()
    servidor = create_server()
    transporte = os.environ.get("MCP_TRANSPORTE", "stdio")
    if transporte == "streamable-http":
        porta = int(os.environ.get("MCP_PORTA", "8000"))
        servidor.run(transport="streamable-http", port=porta)
    else:
        servidor.run()


if __name__ == "__main__":
    main()
