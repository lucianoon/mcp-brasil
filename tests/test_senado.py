import httpx
import respx

from mcp_dados_br.tools import senado

BASE = "https://legis.senado.leg.br/dadosabertos"


def _voto(nome: str, sigla: str) -> dict:
    return {"IdentificacaoParlamentar": {"NomeParlamentar": nome}, "SiglaVoto": sigla}

RESPOSTA_SENADORES = {
    "ListaParlamentarEmExercicio": {
        "Parlamentares": {
            "Parlamentar": [
                {
                    "IdentificacaoParlamentar": {
                        "CodigoParlamentar": "5672",
                        "NomeParlamentar": "Alan Rick",
                        "SiglaPartidoParlamentar": "PSD",
                        "UfParlamentar": "TO",
                    }
                },
                {
                    "IdentificacaoParlamentar": {
                        "CodigoParlamentar": "5555",
                        "NomeParlamentar": "Teste Silva",
                        "SiglaPartidoParlamentar": "PT",
                        "UfParlamentar": "MG",
                    }
                },
            ]
        }
    }
}

RESPOSTA_MATERIAS = {
    "PesquisaBasicaMateria": {
        "Materias": {
            "Materia": [
                {
                    "Codigo": "172333",
                    "Sigla": "PL",
                    "Numero": "00001",
                    "Ano": "2026",
                    "Ementa": "Dispõe sobre a política nacional de segurança hídrica.",
                },
                {
                    "Codigo": "172334",
                    "Sigla": "PL",
                    "Numero": "00002",
                    "Ano": "2026",
                    "Ementa": "Altera a legislação tributária.",
                },
            ]
        }
    }
}

RESPOSTA_VOTACAO = {
    "VotacaoMateria": {
        "Materia": {
            "Votacoes": {
                "Votacao": [
                    {
                        "SessaoPlenaria": {"DataSessao": "2026-02-24"},
                        "DescricaoVotacao": "Votação nominal da matéria em 1º turno.",
                        "DescricaoResultado": "Aprovado",
                        "Votos": {
                            "VotoParlamentar": [
                                _voto("A", "S"),
                                _voto("B", "S"),
                                _voto("C", "N"),
                                _voto("D", "P"),
                            ]
                        },
                    }
                ]
            }
        }
    }
}


async def test_senado_senadores_sem_resultado() -> None:
    with respx.mock:
        respx.get(f"{BASE}/senador/lista/atual.json").mock(
            return_value=httpx.Response(
                200,
                json={"ListaParlamentarEmExercicio": {"Parlamentares": {}}},
            )
        )
        saida = await senado.senado_senadores()
    assert saida == "Nenhum senador encontrado para os filtros informados."


@respx.mock
async def test_senado_senadores_filtra_uf() -> None:
    respx.get(f"{BASE}/senador/lista/atual.json").mock(
        return_value=httpx.Response(200, json=RESPOSTA_SENADORES)
    )
    saida = await senado.senado_senadores(uf="mg")
    assert saida == "1 senadores:\n5555 — Teste Silva (PT/MG)"


@respx.mock
async def test_senado_materias_filtra_palavras_chave() -> None:
    respx.get(f"{BASE}/materia/pesquisa/lista.json").mock(
        return_value=httpx.Response(200, json=RESPOSTA_MATERIAS)
    )
    saida = await senado.senado_materias(sigla="PL", ano=2026, palavras_chave="hídrica")
    assert "172333 — PL 1/2026" in saida
    assert "tributária" not in saida


@respx.mock
async def test_senado_materias_sem_resultado() -> None:
    respx.get(f"{BASE}/materia/pesquisa/lista.json").mock(
        return_value=httpx.Response(200, json={"PesquisaBasicaMateria": {"Materias": {}}})
    )
    saida = await senado.senado_materias(sigla="PL", ano=1999)
    assert saida == "Nenhuma matéria encontrada para os filtros informados."


@respx.mock
async def test_senado_votacoes_placar_e_resultado() -> None:
    respx.get(f"{BASE}/materia/votacoes/144123.json").mock(
        return_value=httpx.Response(200, json=RESPOSTA_VOTACAO)
    )
    saida = await senado.senado_votacoes(144123)
    assert "1 votações da matéria 144123:" in saida
    assert "2026-02-24 — sim: 2 | não: 1 | abst.: 1 — resultado: Aprovado" in saida


@respx.mock
async def test_senado_votacoes_vazias() -> None:
    respx.get(f"{BASE}/materia/votacoes/999.json").mock(
        return_value=httpx.Response(
            200,
            json={"VotacaoMateria": {"Materia": {"Votacoes": {}}}},
        )
    )
    saida = await senado.senado_votacoes(999)
    assert saida == "Nenhuma votação registrada para a matéria 999."
