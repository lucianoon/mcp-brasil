# mcp-dados-br

Servidor **MCP (Model Context Protocol)** que expõe dados públicos brasileiros como ferramentas para assistentes de IA: [Claude Desktop](https://claude.ai/download), Claude Code, Cursor e qualquer cliente MCP.

## Ferramentas disponíveis

| Fonte | Tools | Descrição |
|---|---|---|
| IBGE/SIDRA | `ibge_populacao`, `ibge_pib`, `ibge_municipios`, `ibge_sidra` | População, PIB, busca de municípios e consulta genérica a qualquer agregado SIDRA |
| Banco Central | `bcb_serie`, `bcb_cambio`, `bcb_moedas`, `bcb_focus` | Séries temporais SGS (Selic, IPCA...), cotações PTAX, lista de moedas e expectativas do Boletim Focus |
| INMET | `inmet_estacoes`, `inmet_dados` | Lista de estações meteorológicas e dados horários observados (dados observacionais exigem token) |
| Câmara dos Deputados | `camara_deputados`, `camara_detalhes_deputado`, `camara_proposicoes`, `camara_votacoes_proposicao` | Deputados, proposições legislativas e votações |

Todas as fontes são APIs oficiais abertas — nenhuma chave de API necessária,
exceto os dados horários do INMET (veja abaixo).

## Instalação

Requisitos: [uv](https://docs.astral.sh/uv/) (ou Python 3.12+ com pip).

```bash
git clone https://github.com/lucianoon/mcp-dados-br
cd mcp-dados-br
uv sync
```

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

Sem o token, as demais 13 ferramentas funcionam normalmente.

## Exemplos de uso

Depois de configurar, pergunte diretamente ao assistente:

- "Qual foi o IPCA dos últimos 6 meses?"
- "O que o mercado espera para a Selic nas próximas reuniões?" (Boletim Focus)
- "Quem são os deputados federais de Minas Gerais do partido X?"
- "Qual a população de São Paulo em 2022? E o PIB?"
- "Como está o dólar PTAX nos últimos dias?"
- "Busque projetos de lei de 2025 sobre saúde mental"
- "Quais estações automáticas do INMET existem no Amazonas?"

## Desenvolvimento

```bash
uv sync --dev
uv run pytest
uv run ruff check .
uv run mypy src
```

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
    └── camara.py    # Dados Abertos da Câmara v2
```

- Transporte stdio (padrão MCP desktop)
- Cache TTL de 10 minutos por requisição idêntica
- Retry automático em falhas de rede
- Saídas formatadas como texto legível pelo modelo

## Roadmap

- [x] v0.2 — INMET (estações + observacional com token) e Boletim Focus
- [ ] DOU: busca no Diário Oficial da União (aguardando API pública estável)
- [ ] TSE: resultados eleitorais
- [ ] Publicação no PyPI (`uvx mcp-dados-br`)
- [ ] Transporte streamable-http opcional

## Licença

MIT
