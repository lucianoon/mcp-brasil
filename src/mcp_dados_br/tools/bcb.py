from datetime import date, timedelta
from typing import Any

from mcp_dados_br.http import get_json

_SGS_URL = "https://api.bcb.gov.br/dados/serie"
_OLINDA_URL = "https://olinda.bcb.gov.br/olinda/servico"
_PTAX_URL = f"{_OLINDA_URL}/PTAX/versao/v1/odata"
_FOCUS_URL = f"{_OLINDA_URL}/Expectativas/versao/v1/odata"

_FOCUS_ENTIDADES = {
    "selic": ("ExpectativasMercadoSelic", None),
    "ipca": ("ExpectativasMercadoTop5Inflacao12Meses", "Indicador eq 'IPCA'"),
    "pib": ("ExpectativasMercadoTop5Anuais", "Indicador eq 'PIB Total'"),
    "cambio": ("ExpectativasMercadoTop5Anuais", "Indicador eq 'Câmbio'"),
}


def _data_sgs(iso: str) -> str:
    ano, mes, dia = iso.split("-")
    return f"{dia}/{mes}/{ano}"


def _data_ptax(iso: str) -> str:
    ano, mes, dia = iso.split("-")
    return f"{mes}-{dia}-{ano}"


async def bcb_serie(
    codigo: int,
    data_inicial: str | None = None,
    data_final: str | None = None,
) -> str:
    """Consulta séries temporais do Sistema Gerenciador de Séries (SGS) do Banco Central.

    Args:
        codigo: Código da série SGS. Exemplos: 1178 (Selic meta), 433 (IPCA mensal),
            13522 (IPCA acumulado em 12 meses), 4390 (CDI), 36 (salário mínimo),
            189 (IGP-M), 206 (INPC). Catálogo: https://www3.bcb.gov.br/sgspub/
        data_inicial: Data inicial ISO "AAAA-MM-DD". Padrão: últimos 90 dias.
        data_final: Data final ISO "AAAA-MM-DD". Padrão: hoje.
    """
    fim = date.fromisoformat(data_final) if data_final else date.today()
    inicio = date.fromisoformat(data_inicial) if data_inicial else fim - timedelta(days=90)
    if inicio > fim:
        raise ValueError("data_inicial deve ser anterior ou igual a data_final.")
    url = f"{_SGS_URL}/bcdata.sgs.{codigo}/dados"
    dados: list[dict[str, Any]] = await get_json(url, params={
        "formato": "json",
        "dataInicial": _data_sgs(inicio.isoformat()),
        "dataFinal": _data_sgs(fim.isoformat()),
    })
    if not dados:
        return f"Nenhum dado retornado para a série {codigo} no período informado."
    linhas = [f"{item['data']}: {item['valor']}" for item in dados[-60:]]
    if len(dados) > 60:
        linhas.insert(0, f"Série {codigo}: {len(dados)} registros; exibindo os últimos 60.")
    else:
        linhas.insert(0, f"Série {codigo}:")
    return "\n".join(linhas)


async def bcb_cambio(moeda: str = "USD", dias: int = 7) -> str:
    """Cotações de câmbio PTAX do Banco Central para uma moeda nos últimos N dias.

    Args:
        moeda: Símbolo da moeda (ex.: "USD", "EUR", "GBP"). Use a tool bcb_moedas
            para listar as moedas disponíveis.
        dias: Quantidade de dias úteis de cotação a retornar (padrão 7).
    """
    fim = date.today()
    inicio = fim - timedelta(days=max(dias, 2) + 5)
    url = (
        f"{_PTAX_URL}/CotacaoMoedaPeriodo(moeda=@moeda,"
        f"dataInicial=@dataInicial,dataFinalCotacao=@dataFinalCotacao)"
    )
    dados: dict[str, Any] = await get_json(url, params={
        "@moeda": f"'{moeda.upper()}'",
        "@dataInicial": f"'{_data_ptax(inicio.isoformat())}'",
        "@dataFinalCotacao": f"'{_data_ptax(fim.isoformat())}'",
        "$format": "json",
        "$top": max(dias * 2, 20),
    })
    cotacoes = dados.get("value") or []
    if not cotacoes:
        return (
            f"Nenhuma cotação encontrada para {moeda.upper()}. "
            "Verifique o símbolo com a tool bcb_moedas."
        )
    fechamentos = [c for c in cotacoes if c.get("tipoBoletim") == "Fechamento"]
    base = fechamentos if fechamentos else cotacoes
    ultimas = base[-dias:] if dias < len(base) else base
    compras = [float(c["cotacaoCompra"]) for c in ultimas]
    vendas = [float(c["cotacaoVenda"]) for c in ultimas]
    ultima = ultimas[-1]
    resumo = [
        f"PTAX {moeda.upper()} — última cotação ({ultima['dataHoraCotacao'][:10]}): "
        f"compra R$ {ultima['cotacaoCompra']}, venda R$ {ultima['cotacaoVenda']}",
        f"Período ({len(ultimas)} cotações): compra mín. R$ {min(compras)}, "
        f"máx. R$ {max(compras)}, média R$ {sum(compras) / len(compras):.4f}; "
        f"venda mín. R$ {min(vendas)}, máx. R$ {max(vendas)}",
    ]
    historico = [
        (
            f"{c['dataHoraCotacao'][:10]}: compra R$ {c['cotacaoCompra']} / "
            f"venda R$ {c['cotacaoVenda']}"
        )
        for c in ultimas
    ]
    return "\n".join(resumo + [""] + historico)


async def bcb_moedas() -> str:
    """Lista as moedas com cotação PTAX disponíveis no Banco Central."""
    dados: dict[str, Any] = await get_json(
        f"{_PTAX_URL}/Moedas", params={"$format": "json"}
    )
    moedas = dados.get("value") or []
    linhas = [f"{m['simbolo']} — {m['nomeFormatado']}" for m in moedas]
    return "\n".join(linhas)


def _periodo_focus(registro: dict[str, Any]) -> str:
    if registro.get("Reuniao"):
        return f"reunião {registro['Reuniao']}"
    if registro.get("DataReferencia"):
        return f"referência {registro['DataReferencia']}"
    return "próximos 12 meses"


def _formatar_focus(indicador: str, registros: list[dict[str, Any]]) -> str:
    data_pesquisa = max(str(r.get("Data")) for r in registros)
    do_dia = [r for r in registros if str(r.get("Data")) == data_pesquisa]

    def mediana(r: dict[str, Any]) -> float:
        valor = r.get("Mediana")
        return float(valor) if valor is not None else float("inf")

    ordenados = sorted(do_dia, key=mediana)
    linhas = [
        f"Focus BCB ({data_pesquisa}) — expectativas para {indicador.upper()}:"
    ]
    for r in ordenados:
        partes = [
            _periodo_focus(r),
            f"mediana {r.get('Mediana')}",
            f"média {r.get('Media')}",
            f"mín {r.get('Minimo')}",
            f"máx {r.get('Maximo')}",
        ]
        respondentes = r.get("numeroRespondentes")
        if respondentes:
            partes.append(f"{respondentes} analistas")
        linhas.append(" | ".join(partes))
    return "\n".join(linhas)


async def bcb_focus(indicador: str = "selic") -> str:
    """Expectativas de mercado do Boletim Focus (Boletim Focus) do Banco Central.

    Mostra a projeção média dos analistas de mercado para os próximos períodos.

    Args:
        indicador: Um de: "selic", "ipca", "pib" ou "cambio".
    """
    chave = indicador.strip().casefold()
    entidade_info = _FOCUS_ENTIDADES.get(chave)
    if entidade_info is None:
        validos = ", ".join(sorted(_FOCUS_ENTIDADES))
        raise ValueError(f"Indicador desconhecido: {indicador!r}. Válidos: {validos}")
    entidade, filtro_indicador = entidade_info
    desde = (date.today() - timedelta(days=7)).isoformat()
    filtro = f"Data ge '{desde}'"
    if filtro_indicador:
        filtro += f" and {filtro_indicador}"
    dados: dict[str, Any] = await get_json(
        f"{_FOCUS_URL}/{entidade}",
        params={
            "$format": "json",
            "$filter": filtro,
            "$orderby": "Data desc",
            "$top": 60,
        },
    )
    registros = dados.get("value") or []
    if chave == "selic":
        registros = [r for r in registros if r.get("baseCalculo") == 0]
    if not registros:
        return (
            f"Nenhuma expectativa recente encontrada para {chave}. "
            "O boletim Focus pode não ter sido publicado nos últimos 7 dias."
        )
    return _formatar_focus(chave, registros)
