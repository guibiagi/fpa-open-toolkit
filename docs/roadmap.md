# Roadmap — FP&A Open Toolkit

## v0.1 — MVP ✅ (Completo)

- [x] Estrutura do projeto e tooling (pyproject.toml, Makefile, Ruff)
- [x] Módulo de feriados BR e dias úteis (`utils.dates`)
- [x] Utilitários de IO e formatação (`utils.io`, `utils.formatting`)
- [x] Documentação inicial (README, data dictionary, architecture)
- [x] Dockerfile + .dockerignore
- [x] Gerador de dados sintéticos (6 datasets, seed=42, determinístico)
- [x] Testes do gerador (21 testes)
- [x] Engine de forecast de receita (MA3 + crescimento + sazonalidade, 3 cenários)
- [x] Engine de projeção de fluxo de caixa (90 dias, dias úteis BR, pesos ter/qua/qui)
- [x] Cálculo de KPIs financeiros (20+ métricas: NCG, PMR, PME, PMP, ciclo, cobertura)
- [x] FastAPI core (app/main.py, config via pydantic-settings, lifespan, health)
- [x] API routers (endpoints JSON: overview, forecast, cashflow, working-capital, debt)
- [x] Pages router (6 rotas HTML: index, forecast, cashflow, working-capital, debt, explorer)
- [x] Templates: base.html + Overview + Forecast
- [x] Templates: Cash Flow + Working Capital + Debt
- [x] Templates: Data Explorer + static assets (CSS customizado, Chart.js)
- [x] README final + CI (GitHub Actions: ruff + pytest)
- [ ] Exportação Excel (relatório consolidado com 6 abas) — **issue #8**

> 🟡 1 item pendente da v0.1: exportação Excel. **196 testes, 0 falhas.**

## v0.2 — Upload de Dados Reais

| Entregável | Descrição |
|-----------|-----------|
| Upload CSV/Excel | Importar dados reais via interface web |
| Validação de schema | Verificar colunas obrigatórias antes de importar |
| Modo misto | Trabalhar com dados sintéticos + reais simultaneamente |
| Cache de upload | Manter dados importados entre sessões (session storage) |

## v0.3 — Modelos Avançados de Forecast

| Entregável | Descrição |
|-----------|-----------|
| Prophet | Forecast com Facebook Prophet (sazonalidade + feriados automáticos) |
| Holt-Winters | Suavização exponencial tripla |
| Ridge Regression | Regressão com regularização para múltiplas features |
| Ensemble | Combinação ponderada dos modelos acima |
| Comparação de modelos | Gráfico comparativo e métricas de erro (MAE, RMSE, MAPE) |

## v0.4 — Autenticação e Multitenancy

| Entregável | Descrição |
|-----------|-----------|
| Login simples | Autenticação por usuário/senha (JWT ou session) |
| Proteção de rotas | Páginas e APIs protegidas por login |
| Multitenancy | Isolamento de dados por empresa/usuário |
| Onboarding | Primeiro acesso guiado |

## v0.5 — Persistência e Escalabilidade

| Entregável | Descrição |
|-----------|-----------|
| Docker Compose | App + PostgreSQL + adminer |
| SQLAlchemy | Modelos ORM para dados financeiros |
| Migrations | Alembic para versionamento de schema |
| Background tasks | Processamento assíncrono de forecasts longos |
| Cache | Redis para endpoints de API mais lentos |

## v0.6 — Relatórios PDF e Alertas

| Entregável | Descrição |
|-----------|-----------|
| Relatório PDF | Exportação via WeasyPrint ou Playwright |
| Template de relatório | Layout profissional para conselho/board |
| Alertas de caixa | Notificação quando saldo projetado < limite |
| Newsletter mensal | Relatório automático por e-mail |
| Dashboard mobile | Layout responsivo para celular |

## Ideias Futuras (Não Prioritárias)

- Integração com ERPs via API (Bling, Omie, etc.)
- Conciliação bancária automatizada
- Simulação de cenários (M&A, novos produtos)
- Inteligência artificial para detecção de anomalias
- Plugins e extensões por contribuição da comunidade
- Tradução para inglês

---

*Roadmap sujeito a alterações conforme feedback da comunidade.*
