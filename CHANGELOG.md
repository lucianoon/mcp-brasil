# Changelog

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/)
e versionamento semântico.

## [Não lançado]

### Planejado

- Publicação no PyPI (`uvx mcp-dados-br`)
- Busca no Diário Oficial da União (aguardando API pública estável)
- Resultados eleitorais do TSE

## [0.5.1] — 2026-08-25

### Adicionado

- `server.json` para o MCP Registry oficial e `smithery.yaml` para a Smithery
- Workflow publica automaticamente no MCP Registry após o deploy no PyPI
- Marcador de verificação de propriedade no README (`mcp-name`)

## [0.5.0] — 2026-08-25

### Adicionado

- Módulo Senado Federal sobre a API LegisSaber:
  `senado_senadores` (81 senadores, filtros por UF e nome),
  `senado_materias` (pesquisa por sigla, ano e palavras-chave) e
  `senado_votacoes` (placar nominal e resultado por sessão)

### Adotado do benchmark DeHor Labs

- Badges de CI/Python/licença no README
- `CHANGELOG.md` (este arquivo)
- Logging opcional em stderr via `MCP_LOG_LEVEL`
- `CONTRIBUTING.md` e templates de issue

## [0.4.0] — 2026-08-25

### Adicionado

- Tool `camara_tramitacao`: histórico de tramitação de uma proposição
- Atalhos nomeados em `bcb_serie`: `selic`, `cdi`, `ipca`, `ipca_12m`,
  `igpm`, `inpc`, `salario_minimo`
- Dockerfile com transporte streamable-http padrão
- Dependabot para GitHub Actions

### Alterado

- Timeout HTTP de 15s para 30s com 3 tentativas (APIs governamentais lentas)

## [0.3.0] — 2026-08-25

### Adicionado

- Tool `camara_agenda`: eventos da Câmara dos próximos dias
- Transporte `streamable-http` configurável via `MCP_TRANSPORTE`
- Job de integração no CI (cron semanal) contra as APIs reais

## [0.2.0] — 2026-08-25

### Adicionado

- Tools `inmet_estacoes` (aberta) e `inmet_dados` (requer token INMET opcional)
- Tool `bcb_focus`: expectativas do Boletim Focus para Selic, IPCA, PIB e câmbio

### Corrigido

- Encoding de queries OData (`%20` em vez de `+`) para o serviço Olinda do BCB

## [0.1.0] — 2026-08-24

### Adicionado

- Servidor MCP inicial com 11 ferramentas: IBGE/SIDRA (população, PIB,
  municípios, consulta genérica), Banco Central (séries SGS, PTAX, moedas)
  e Câmara dos Deputados (deputados, proposições, votações)
- Cache TTL de 10 minutos e retry automático
- CI em Python 3.12 e 3.14 (ruff, mypy strict, pytest)
