import os
from datetime import date, timedelta
from typing import Any

from mcp_dados_br.http import get_json

_INMET_URL = "https://apitempo.inmet.gov.br"

_TIPOS = {
    "t": "T",
    "automatica": "T",
    "automaticas": "T",
    "m": "M",
    "convencional": "M",
    "convencionais": "M",
}

_MAX_LINHAS = 40

_CAMPOS_OBSERVADOS = [
    ("TEM_INS", "temp °C"),
    ("UMD_INS", "ur %"),
    ("VEN_VEL", "vento m/s"),
    ("PRE_INS", "pressão hPa"),
    ("CHUVA", "chuva mm"),
]


def _normalizar_tipo(tipo: str) -> str:
    codigo = _TIPOS.get(tipo.strip().casefold())
    if codigo is None:
        validos = ", ".join(sorted(set(_TIPOS.values())))
        raise ValueError(
            f"Tipo desconhecido: {tipo!r}. "
            f"Use T (automática) ou M (convencional). Válidos: {validos}"
        )
    return codigo


async def inmet_estacoes(tipo: str = "T", uf: str | None = None) -> str:
    """Lista estações meteorológicas do INMET (não requer autenticação).

    Args:
        tipo: "T" para estações automáticas ou "M" para convencionais.
        uf: Sigla opcional da UF para filtrar, ex.: "SP".
    """
    codigo_tipo = _normalizar_tipo(tipo)
    estacoes: list[dict[str, Any]] = await get_json(f"{_INMET_URL}/estacoes/{codigo_tipo}")
    if uf:
        sigla = uf.strip().upper()
        estacoes = [e for e in estacoes if e.get("SG_ESTADO") == sigla]
    operantes = [e for e in estacoes if e.get("CD_SITUACAO") != "Desativada"]
    rotulo = "automáticas" if codigo_tipo == "T" else "convencionais"
    if not operantes:
        return f"Nenhuma estação {rotulo} encontrada para os filtros informados."
    linhas = [f"{len(operantes)} estações {rotulo}:"]
    for e in operantes[:_MAX_LINHAS]:
        altitude = e.get("VL_ALTITUDE")
        altitude_txt = f", {float(altitude):.0f} m" if altitude else ""
        capital = " [capital]" if e.get("FL_CAPITAL") == "S" else ""
        linhas.append(
            f"{e.get('CD_ESTACAO')} — {e.get('DC_NOME')} "
            f"({e.get('SG_ESTADO')}{capital}{altitude_txt})"
        )
    if len(operantes) > _MAX_LINHAS:
        linhas.append(f"... (+{len(operantes) - _MAX_LINHAS} estações omitidas)")
    return "\n".join(linhas)


def _formatar_registro(registro: dict[str, Any]) -> str:
    data_m = str(registro.get("DT_MEDICAO", "?"))
    hora_m = str(registro.get("HR_MEDICAO", "")).zfill(4)
    momento = f"{data_m} {hora_m[:2]}:{hora_m[2:]}" if hora_m else data_m
    partes = [
        f"{rotulo} {registro[campo]}"
        for campo, rotulo in _CAMPOS_OBSERVADOS
        if registro.get(campo) not in (None, "")
    ]
    return f"{momento} UTC — " + (" | ".join(partes) if partes else "sem medições")


async def inmet_dados(estacao: str, dias: int = 2) -> str:
    """Dados horários observados de uma estação automática do INMET (últimos dias).

    Requer o ambiente INMET_TOKEN com token fornecido pelo INMET
    (solicite em https://portal.inmet.gov.br). Sem token, use inmet_estacoes.

    Args:
        estacao: Código da estação, ex.: "A001". Liste códigos com inmet_estacoes.
        dias: Quantidade de dias retroativos a consultar (padrão 2, máximo 7).
    """
    token = os.environ.get("INMET_TOKEN")
    if not token:
        return (
            "Consulta indisponível: os dados observacionais do INMET exigem um token. "
            "Solicite em https://portal.inmet.gov.br e configure a variável de "
            "ambiente INMET_TOKEN no servidor MCP."
        )
    fim = date.today()
    inicio = fim - timedelta(days=min(max(dias, 1), 7))
    url = (
        f"{_INMET_URL}/token/estacao/{inicio.isoformat()}/"
        f"{fim.isoformat()}/{estacao.upper()}/{token}"
    )
    registros: list[dict[str, Any]] = await get_json(url)
    if not registros:
        return f"Nenhum dado retornado para a estação {estacao.upper()} no período."
    ultimos = registros[-72:]
    cabecalho = (
        f"Estação {estacao.upper()}: {len(registros)} registros; "
        f"exibindo os últimos {len(ultimos)}:"
    )
    return "\n".join([cabecalho] + [_formatar_registro(r) for r in ultimos])
