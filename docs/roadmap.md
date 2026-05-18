# Roadmap — FP&A Open Toolkit

## v0.1 — MVP (atual)

- [x] Estrutura do projeto e tooling (pyproject.toml, Makefile, Ruff)
- [x] Módulo de feriados BR e dias úteis (`utils.dates`)
- [x] Utilitários de IO e formatação (`utils.io`, `utils.formatting`)
- [x] Documentação inicial (README, data dictionary, architecture)
- [x] Dockerfile + .dockerignore
- [ ] Gerador de dados sintéticos (6 datasets)
- [ ] Testes do gerador
- [ ] Engine de forecast de receita
- [ ] Engine de projeção de fluxo de caixa
- [ ] Cálculo de KPIs financeiros
- [ ] Exportação Excel (relatório consolidado)
- [ ] FastAPI core (app/main.py, settings, logging)
- [ ] API routers (endpoints JSON)
- [ ] Pages router (rotas HTML)
- [ ] Templates: base.html + Overview + Forecast
- [ ] Templates: Cash Flow + Working Capital + Debt
- [ ] Templates: Data Explorer + static assets
- [ ] README final + CI

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
