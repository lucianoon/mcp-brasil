# mcp-dados-br

[![CI](https://github.com/lucianoon/mcp-dados-br/actions/workflows/ci.yml/badge.svg)](https://github.com/lucianoon/mcp-dados-br/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/mcp-dados-br?color=2e7d32&label=PyPI)](https://pypi.org/project/mcp-dados-br/)
[![Python](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org)
[![Licença: MIT](https://img.shields.io/badge/licen%C3%A7a-MIT-green.svg)](LICENSE)

Servidor **MCP (Model Context Protocol)** que expõe dados públicos brasileiros como ferramentas para assistentes de IA: [Claude Desktop](https://claude.ai/download), Claude Code, Cursor e qualquer cliente MCP.

## Instalação

A forma mais simples, sem instalar nada permanentemente:

```bash
uvx mcp-dados-br
```

Configuração no Claude Desktop:

```json
{
  "mcpServers": {
    "dados-brasil": {
      "command": "uvx",
      "args": ["mcp-dados-br"]
    }
  }
}
```

Ou no Claude Code:

```bash
claude mcp add dados-brasil -- uvx mcp-dados-br
```

### A partir do código-fonte

```bash
git clone https://github.com/lucianoon/mcp-dados-br
cd mcp-dados-br
uv sync
```

## Ferramentas disponíveis

| Fonte | Tools | Descrição |
|---|---|---|
| IBGE/SIDRA | `ibge_populacao`, `ibge_pib`, `ibge_municipios`, `ibge_sidra` | População, PIB, busca de municípios e consulta genérica a qualquer agregado SIDRA |
| Banco Central | `bcb_serie`, `bcb_cambio`, `bcb_moedas`, `bcb_focus` | Séries SGS com atalhos nomeados (`selic`, `ipca`, `cdi`...), cotações PTAX, lista de moedas e expectativas do Boletim Focus |
| INMET | `inmet_estacoes`, `inmet_dados` | Lista de estações meteorológicas e dados horários observados (dados observacionais exigem token) |
| Câmara dos Deputados | `camara_deputados`, `camara_detalhes_deputado`, `camara_proposicoes`, `camara_votacoes_proposicao`, `camara_agenda`, `camara_tramitacao` | Deputados, proposições, votações, agenda e tramitações |
| Senado Federal | `senado_senadores`, `senado_materias`, `senado_votacoes` | Senadores em exercício, matérias legislativas e votações nominais com placar |

Todas as fontes são APIs oficiais abertas — nenhuma chave de API necessária,
exceto os dados horários do INMET (veja abaixo).

## Configuração

### Claude Desktop / Cursor

Adicione ao arquivo de configuração (`claude_desktop_config.json` ou `mcp.json`):

```json
{
  "mcpServers": {
    "mcp-dados-br": {
      "command": "uv",
      "args": ["run", "--directory", "/caminho/para/mcp-dados-br", "mcp-dados-br"]
    }
  }
}
```

### Claude Code

```bash
claude mcp add mcp-dados-br -- uv run --directory /caminho/para/mcp-dados-br mcp-dados-br
```

## Token opcional do INMET

A listagem de estações (`inmet_estacoes`) é aberta. Já os **dados horários
observados** (`inmet_dados`) exigem um token fornecido pelo INMET — solicite em
[portal.inmet.gov.br](https://portal.inmet.gov.br) e configure a variável de
ambiente no cliente MCP:

```json
{
  "mcpServers": {
    "mcp-dados-br": {
      "command": "uv",
      "args": ["run", "--directory", "/caminho/para/mcp-dados-br", "mcp-dados-br"],
      "env": { "INMET_TOKEN": "seu-token" }
    }
  }
}
```

Sem o token, as demais 14 ferramentas funcionam normalmente.

## Transporte streamable-http

Além do stdio padrão, o servidor pode rodar em modo HTTP remoto:

```bash
MCP_TRANSPORTE=streamable-http MCP_PORTA=8000 mcp-dados-br
```

Aponte clientes para `http://localhost:8000/mcp`. Útil para Docker ou
compartilhar o servidor na rede local.

### Docker

```bash
docker build -t mcp-dados-br .
docker run -p 8000:8000 -e INMET_TOKEN=seu-token mcp-dados-br
```

## Exemplos de uso

Depois de configurar, pergunte diretamente ao assistente:

- "Qual foi o IPCA dos últimos 6 meses?"
- "O que o mercado espera para a Selic nas próximas reuniões?" (Boletim Focus)
- "Quem são os deputados federais de Minas Gerais do partido X?"
- "Qual a população de São Paulo em 2022? E o PIB?"
- "Como está o dólar PTAX nos últimos dias?"
- "Busque projetos de lei de 2025 sobre saúde mental"
- "O que está na agenda da Câmara esta semana?"
- "Como o Senado votou a PEC X? Qual o placar?"
- "Quem são os senadores de Minas Gerais?"
- "Quais estações automáticas do INMET existem no Amazonas?"

## Desenvolvimento

```bash
uv sync --dev
uv run pytest              # suíte unitária (mocks)
uv run pytest -m integration   # consulta as APIs reais
uv run ruff check .
uv run mypy src
```

Logs de depuração: configure `MCP_LOG_LEVEL=DEBUG` no cliente MCP.
Para contribuir, leia o [CONTRIBUTING.md](CONTRIBUTING.md).

### Arquitetura

```
src/mcp_dados_br/
├── server.py        # Servidor MCP e registro das tools
├── http.py          # Cliente HTTP compartilhado, retry e tratamento de erros
├── cache.py         # Cache TTL em memória para as respostas das APIs
└── tools/
    ├── ibge.py      # SIDRA v3 + localidades v1
    ├── bcb.py       # SGS + Olinda (PTAX e Boletim Focus)
    ├── inmet.py     # Estações e dados observacionais
    ├── camara.py    # Dados Abertos da Câmara v2
    └── senado.py    # Dados Abertos do Senado (LegisSaber)
```

- Transporte stdio (padrão MCP desktop)
- Cache TTL de 10 minutos por requisição idêntica
- Retry automático em falhas de rede
- Saídas formatadas como texto legível pelo modelo

## Roadmap

- [x] v0.2 — INMET (estações + observacional com token) e Boletim Focus
- [x] v0.3 — Agenda da Câmara, transporte streamable-http e testes de integração agendados no CI
- [x] v0.4 — Tramitações, atalhos nomeados no SGS, imagem Docker
- [ ] Publicação no PyPI (`uvx mcp-dados-br`)
- [ ] DOU: busca no Diário Oficial da União (aguardando API pública estável)
- [ ] TSE: resultados eleitorais

## Licença

MIT
