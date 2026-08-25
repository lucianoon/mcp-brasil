# Contribuindo

Obrigado pelo interesse! O projeto prioriza ferramentas confiáveis sobre
APIs públicas brasileiras, com código tipado e testado.

## Ambiente de desenvolvimento

Requisitos: [uv](https://docs.astral.sh/uv/) e Python 3.12+.

```bash
git clone https://github.com/lucianoon/mcp-dados-br
cd mcp-dados-br
uv sync --dev
uv run pytest          # suíte unitária (mocks, rápida)
uv run ruff check .
uv run mypy src
```

Para validar contra as APIs reais (opcional, mais lento):

```bash
uv run pytest -m integration
```

## Antes de abrir um PR

1. Crie uma issue antes para mudanças grandes ou novas fontes de dados —
   vale alinhar escopo primeiro
2. Adicione testes com `respx` para toda tool nova (veja `tests/` como exemplo)
3. Docstrings das tools viram as descrições que o LLM vê: escreva-as em
   **português**, com `Args:` documentando cada parâmetro
4. Mantenha `ruff check .` e `mypy src` sem erros
5. Atualize o `CHANGELOG.md` na seção **Não lançado**

## Convenções do projeto

- Código, docstrings e mensagens de usuário em português brasileiro
- Tools retornam texto legível por LLMs, nunca JSON cru
- Toda chamada HTTP passa por `mcp_dados_br.http.get_json` (cache + retry)
- Nenhuma chave de API obrigatória; tokens opcionais via variáveis de ambiente

## Reportando bugs

Use o template de issue. Inclua a tool chamada, os parâmetros e o erro
completo (ative logs com `MCP_LOG_LEVEL=DEBUG`).
