# mcp-brasil

Servidor **MCP (Model Context Protocol)** que expõe dados públicos brasileiros como ferramentas para assistentes de IA: [Claude Desktop](https://claude.ai/download), Claude Code, Cursor e qualquer cliente MCP.

## Ferramentas disponíveis

| Fonte | Tools | Descrição |
|---|---|---|
| IBGE/SIDRA | `ibge_populacao`, `ibge_pib`, `ibge_municipios`, `ibge_sidra` | População, PIB, busca de municípios e consulta genérica a qualquer agregado SIDRA |
| Banco Central | `bcb_serie`, `bcb_cambio`, `bcb_moedas` | Séries temporais SGS (Selic, IPCA, CDI...), cotações PTAX e lista de moedas |
| Câmara dos Deputados | `camara_deputados`, `camara_detalhes_deputado`, `camara_proposicoes`, `camara_votacoes_proposicao` | Deputados, proposições legislativas e votações |

Todas as fontes são APIs oficiais abertas — nenhuma chave de API necessária.

## Instalação

Requisitos: [uv](https://docs.astral.sh/uv/) (ou Python 3.12+ com pip).

```bash
git clone https://github.com/lucianoon/mcp-brasil
cd mcp-brasil
uv sync
```

## Configuração

### Claude Desktop / Cursor

Adicione ao arquivo de configuração (`claude_desktop_config.json` ou `mcp.json`):

```json
{
  "mcpServers": {
    "mcp-brasil": {
      "command": "uv",
      "args": ["run", "--directory", "/caminho/para/mcp-brasil", "mcp-brasil"]
    }
  }
}
```

### Claude Code

```bash
claude mcp add mcp-brasil -- uv run --directory /caminho/para/mcp-brasil mcp-brasil
```

## Exemplos de uso

Depois de configurar, pergunte diretamente ao assistente:

- "Qual foi o IPCA dos últimos 6 meses?"
- "Quem são os deputados federais de Minas Gerais do partido X?"
- "Qual a população de São Paulo em 2022? E o PIB?"
- "Como está o dólar PTAX nos últimos dias?"
- "Busque projetos de lei de 2025 sobre saúde mental"

## Desenvolvimento

```bash
uv sync --dev
uv run pytest
uv run ruff check .
uv run mypy src
```

### Arquitetura

```
src/mcp_brasil/
├── server.py        # Servidor MCP e registro das tools
├── http.py          # Cliente HTTP compartilhado, retry e tratamento de erros
├── cache.py         # Cache TTL em memória para as respostas das APIs
└── tools/
    ├── ibge.py      # SIDRA v3 + localidades v1
    ├── bcb.py       # SGS + Olinda/PTAX
    └── camara.py    # Dados Abertos da Câmara v2
```

- Transporte stdio (padrão MCP desktop)
- Cache TTL de 10 minutos por requisição idêntica
- Retry automático em falhas de rede
- Saídas formatadas como texto legível pelo modelo

## Roadmap

- [ ] INMET: dados climáticos por estação
- [ ] DOU: busca no Diário Oficial da União
- [ ] TSE: resultados eleitorais
- [ ] Publicação no PyPI (`uvx mcp-brasil`)
- [ ] Transporte streamable-http opcional

## Licença

MIT
