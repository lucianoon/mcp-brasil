from datetime import date, timedelta
from typing import Any

from mcp_brasil.http import get_json

_SGS_URL = "https://api.bcb.gov.br/dados/serie"
_PTAX_URL = "https://olinda.bcb.gov.br/olinda/servico/PTAX/versao/v1/odata"


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
