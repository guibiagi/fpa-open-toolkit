# Arquitetura — FP&A Open Toolkit

## Visão Geral

O FP&A Open Toolkit é uma aplicação web **server-side** com renderização HTML via Jinja2 e interatividade via HTMX. O estado da aplicação é mantido exclusivamente no servidor — não há framework JavaScript no cliente.

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Browser    │────▶│  FastAPI (App)   │────▶│  Engines (src/)  │
│  (HTMX +     │     │  + Jinja2        │     │  ✅ forecasting  │
│   Chart.js)  │◀────│  + Static        │◀────│  ✅ cashflow     │
│              │     │                  │     │  ✅ kpis         │
└──────────────┘     │  /api/* → JSON   │     │  🟡 export       │
                     │  /*     → HTML   │     └──────────────────┘
                     └──────────────────┘              │
                     │  app/main.py                    ▼
                     │  app/config.py         ┌──────────────────┐
                     │  app/routers/          │  data/           │
                     └──────────────────┘     │  synthetic/      │
                                              │  outputs/        │
                                              └──────────────────┘
```

## Decisões Arquiteturais

### 1. Server-Side Rendering (SSR) com HTMX

Em vez de um SPA (React, Vue), optamos por SSR com Jinja2 + HTMX:

- **Manutenção 100% Python** — sem código JS complexo
- **Atualizações parciais** — HTMX troca apenas o trecho necessário do DOM
- **Zero estado no cliente** — formulários POST com query parameters

### 2. Separação Dados × Engines × Apresentação

| Camada | Responsabilidade | Exemplo |
|--------|-----------------|---------|
| `data/` | Dados estáticos (CSV) | `faturamento_historico.csv` |
| `src/` | Lógica de negócio (engines) | `revenue_forecast.py` |
| `app/` | Apresentação (FastAPI + Jinja2) | `templates/forecast.html` |

### 3. Endpoints REST para Dados

Toda página HTML consome dados via `GET /api/*` (JSON) — os mesmos endpoints podem ser usados para integração externa.

**Endpoints implementados:**

| Rota | Descrição | Engine |
|------|-----------|--------|
| `GET /api/overview` | Cards do dashboard (receita, NCG, dívida) | `kpis` |
| `GET /api/forecast` | Histórico + projeção 12 meses | `forecasting` |
| `GET /api/cashflow` | Fluxo de caixa diário 90 dias | `cashflow` |
| `GET /api/working-capital` | Capital de giro e ciclo financeiro | `kpis` |
| `GET /api/debt` | Endividamento e cobertura de juros | `kpis` |

### 4. Determinismo

`numpy.random.default_rng(seed=42)` garante que os dados sintéticos são idênticos entre execuções. Essencial para testes não-flaky e CI.

### 5. Feriados Brasileiros

Uso da biblioteca `holidays` com `subdiv=None` (feriados nacionais). Sábados, domingos e feriados são identificados via `is_business_day()` no módulo `utils/dates.py`.

### 6. Formatação na Apresentação

Valores financeiros são armazenados como `float` (unidade: R$). A formatação BRL (separadores brasileiros) ocorre apenas na camada de template/app, via `utils/formatting.py`.

### 7. Configuração por Ambiente

`app/config.py` usa `pydantic-settings` com `.env` file. Variáveis: `SEED`, `DATA_DIR`, `ENV`, `HOST`, `PORT`. O lifespan do FastAPI gera dados sintéticos automaticamente se ausentes.

## Fluxo de Dados (Exemplo: Forecast)

```
1. Browser GET /forecast?scenario=base&horizon=12
       │
2. FastAPI router → pages.py renderiza forecast.html
       │
3. Template HTMX dispara GET /api/forecast?scenario=base&horizon=12
       │
4. API router → chama src/forecasting/revenue_forecast.py
       │
5. Engine lê data/synthetic/faturamento_historico.csv
       │
6. Retorna JSON com histórico + forecast (3 cenários)
       │
7. HTMX substitui o gráfico e tabela no DOM
       │
8. Chart.js renderiza o gráfico com novos dados
```

## Stack Tecnológica

| Camada | Tecnologia | Motivo |
|--------|-----------|--------|
| Backend | FastAPI | Performance, tipagem, OpenAPI automática |
| Templates | Jinja2 | Padrão FastAPI, herança de templates |
| Interatividade | HTMX | Atualizações parciais sem SPA |
| Gráficos | Chart.js (CDN) | Leve, open source |
| Estilo | TailwindCSS (CDN) | MVP rápido |
| Dados | Pandas + NumPy | Padrão em análise financeira |
| Excel | openpyxl | Exportação multi-aba |
| Feriados | holidays (BR) | Regras oficiais brasileiras |
| Config | pydantic-settings | Tipagem e validação de settings |
| Testes | pytest + pytest-cov | 196 testes, fixtures determinísticas |
| CI | GitHub Actions | Ruff lint + pytest |
| Linter | Ruff | Velocidade, zero config |
| Task Runner | Makefile | Comandos padronizados |

## Segurança

- **Nenhum dado real** — todos os datasets são sintéticos
- **Sem autenticação** no MVP (público para demonstração)
- **Sem banco de dados** no MVP — dados em CSV, state em memória
- **Sem upload de arquivos** no MVP (previsto para v0.2)
- **Headers de segurança** não configurados no MVP (previsto para v0.4)

## Limitações Conhecidas (MVP v0.1)

- Dados sintéticos apenas (sem upload real)
- Forecast por média móvel simples (modelos avançados na v0.3)
- Sem autenticação ou multitenancy
- Sem persistência entre reinícios (dados regenerados no startup)
- Português brasileiro como idioma principal da interface
- Exportação Excel ainda não implementada (issue #8)
