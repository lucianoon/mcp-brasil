from typing import Any

from mcp_dados_br.http import get_json

_BASE_URL = "https://dadosabertos.camara.leg.br/api/v2"

_TRUNCAR = 140


def _truncar(texto: str | None, limite: int = _TRUNCAR) -> str:
    if not texto:
        return ""
    if len(texto) <= limite:
        return texto
    return f"{texto[:limite]}..."


async def camara_deputados(
    uf: str | None = None,
    partido: str | None = None,
    nome: str | None = None,
    legislatura: int | None = None,
) -> str:
    """Lista deputados federais da Câmara com filtros opcionais.

    Args:
        uf: Sigla da unidade federativa, ex.: "SP", "MG".
        partido: Sigla do partido, ex.: "PT", "PSDB".
        nome: Nome (total ou parcial) do parlamentar.
        legislatura: Número da legislatura (ex.: 57 para a atual). Padrão: atual.
    """
    dados: dict[str, Any] = await get_json(
        f"{_BASE_URL}/deputados",
        params={
            "siglaUf": uf.upper() if uf else None,
            "siglaPartido": partido.upper() if partido else None,
            "nome": nome,
            "idLegislatura": legislatura,
            "itens": 20,
        },
    )
    deputados = dados.get("dados") or []
    if not deputados:
        return "Nenhum deputado encontrado para os filtros informados."
    linhas = [
        f"{d['id']} — {d['nome']} ({d['siglaPartido']}/{d['siglaUf']})"
        for d in deputados
    ]
    return "\n".join(linhas)


async def camara_detalhes_deputado(id_deputado: int) -> str:
    """Detalhes de um deputado federal pelo ID: nome civil, partido, UF e gabinete.

    Args:
        id_deputado: ID numérico do deputado (obtido via camara_deputados).
    """
    dados: dict[str, Any] = await get_json(f"{_BASE_URL}/deputados/{id_deputado}")
    conteudo = dados.get("dados") or {}
    ultimo = conteudo.get("ultimoStatus") or {}
    if not ultimo:
        return f"Nenhum deputado encontrado com o ID {id_deputado}."
    gabinete = ultimo.get("gabinete") or {}
    linhas = [
        f"Nome eleitoral: {ultimo.get('nomeEleitoral')}",
        f"Nome civil: {conteudo.get('nomeCivil')}",
        f"Situação: {ultimo.get('situacao')}",
        f"Partido/UF: {ultimo.get('siglaPartido')}/{ultimo.get('siglaUf')}",
        f"E-mail: {ultimo.get('email') or 'não informado'}",
        (
            f"Gabinete: {gabinete.get('predio', '?')}, sala {gabinete.get('sala', '?')}, "
            f"andar {gabinete.get('andar', '?')}, tel. {gabinete.get('telefone', '?')}"
        ),
        f"Foto: {ultimo.get('urlFoto')}",
    ]
    return "\n".join(linhas)


async def camara_proposicoes(
    ano: int | None = None,
    palavras_chave: str | None = None,
    sigla_tipo: str | None = None,
) -> str:
    """Busca proposições legislativas na Câmara (projetos de lei, emendas etc.).

    Args:
        ano: Ano de apresentação, ex.: 2025.
        palavras_chave: Palavras-chave na ementa, ex.: "saude mental".
        sigla_tipo: Sigla do tipo, ex.: "PL", "PEC", "MPV".
    """
    dados: dict[str, Any] = await get_json(
        f"{_BASE_URL}/proposicoes",
        params={
            "ano": ano,
            "keywords": palavras_chave,
            "siglaTipo": sigla_tipo.upper() if sigla_tipo else None,
            "itens": 10,
        },
    )
    proposicoes = dados.get("dados") or []
    if not proposicoes:
        return "Nenhuma proposição encontrada para os filtros informados."
    linhas = [
        f"{p['id']} — {p['siglaTipo']} {p['numero']}/{p['ano']} — {_truncar(p.get('ementa'))}"
        for p in proposicoes
    ]
    return "\n".join(linhas)


async def camara_votacoes_proposicao(id_proposicao: int) -> str:
    """Lista as votações realizadas para uma proposição específica da Câmara.

    Args:
        id_proposicao: ID numérico da proposição (obtido via camara_proposicoes).
    """
    dados: dict[str, Any] = await get_json(
        f"{_BASE_URL}/votacoes",
        params={"idProposicao": id_proposicao, "itens": 15},
    )
    votacoes = dados.get("dados") or []
    if not votacoes:
        return f"Nenhuma votação encontrada para a proposição {id_proposicao}."
    linhas = [
        f"{v['id']} — {v.get('data', '?')} — "
        f"{_truncar(v.get('descricao') or v.get('aprovacao') or 'sem descrição')}"
        for v in votacoes
    ]
    return "\n".join(linhas)
