# FP&A Open Toolkit

> Análise financeira open source para pequenas e médias empresas industriais.

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/guibiagi/fpa-open-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/guibiagi/fpa-open-toolkit/actions)

---

O **FP&A Open Toolkit** é uma aplicação open source em Python para simular e visualizar rotinas de **Financial Planning & Analysis (FP&A)** em uma PME industrial, usando **dados sintéticos** (determinísticos, seed=42).

Inclui: forecast de faturamento com 3 cenários, projeção de fluxo de caixa diário (90 dias, dias úteis BR), análise de capital de giro (NCG, PMR, PME, PMP), 20+ KPIs financeiros e dashboard interativo via **FastAPI + HTMX + Chart.js**.

> *Projeto open source. Dados sintéticos. Não substitui consultoria financeira profissional.*

---

## Funcionalidades

| Módulo | Descrição | Status |
|--------|-----------|--------|
| 📊 Gerador de dados sintéticos | 6 datasets realistas para PME industrial (seed=42, determinístico) | ✅ |
| 📈 Forecast de receita | Projeção 12 meses com cenários Base/Otimista/Pessimista | ✅ |
| 💰 Fluxo de caixa projetado | 90 dias com regras de dias úteis e feriados BR | ✅ |
| 📐 KPIs financeiros | NCG, ciclo financeiro, endividamento, cobertura de juros | ✅ |
| 🌐 Dashboard web | FastAPI + HTMX + Chart.js + TailwindCSS | ✅ |
| 📎 Exportação Excel | Relatório consolidado com 6 abas formatadas | 🟡 |

> ✅ = Pronto · 🟡 = Em andamento

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | FastAPI |
| Templates | Jinja2 + HTMX |
| Gráficos | Chart.js (CDN) |
| Estilo | TailwindCSS (CDN) |
| Dados | Pandas + NumPy |
| Excel | openpyxl |
| Feriados BR | holidays |
| Testes | pytest + pytest-cov |
| Linter | Ruff |
| Task Runner | Makefile |

## Estrutura do Projeto

```
fpa-open-toolkit/
├── pyproject.toml
├── README.md
├── LICENSE (MIT)
├── Makefile
├── Dockerfile
├── .dockerignore
├── data/
│   ├── synthetic/          # CSVs gerados (deterministicamente)
│   └── outputs/            # Resultados dos engines (forecast, fluxo, etc.)
├── src/
│   ├── data_generation/    # Synthetic data generator (6 datasets)
│   ├── forecasting/        # Revenue forecast engine (3 cenários)
│   ├── cashflow/           # Cash flow projection engine (90 dias)
│   ├── kpis/               # Financial KPI calculations (20+ métricas)
│   ├── utils/              # Feriados BR, IO, formatação
│   └── export/             # Exportação Excel
├── app/
│   ├── main.py             # FastAPI app (lifespan, health, exception handlers)
│   ├── config.py           # Settings via pydantic-settings
│   ├── routers/            # Rotas HTML (pages) e JSON (api, export)
│   ├── templates/          # Jinja2 templates (6 páginas)
│   └── static/             # CSS e JS customizados
├── tests/                  # 196 testes pytest
├── docs/                   # Documentação
└── .github/workflows/      # CI (ruff + pytest)
```

## Lógica Financeira

### Forecast de Receita

Modelo simples e interpretável (MVP):

1. **Média móvel** dos últimos 3 meses de faturamento
2. **Crescimento médio** dos últimos 12 meses
3. **Índice de sazonalidade** por mês (calculado sobre 48 meses históricos)
4. **3 cenários**: Base | Otimista (+10%) | Pessimista (−10%)

### Capital de Giro & Ciclo Financeiro

```
NCG = Contas a Receber + Estoque − Contas a Pagar
Ciclo Financeiro = PMR + PME − PMP
```

Onde:
- **PMR** = Prazo Médio de Recebimento (dias)
- **PME** = Prazo Médio de Estoque (dias, via custo de vendas)
- **PMP** = Prazo Médio de Pagamento (dias)

### Fluxo de Caixa

- Projeção diária por 90 dias corridos
- Distribuição ponderada do forecast mensal em dias úteis (ter/qua/qui com peso maior)
- Títulos abertos e vencidos distribuídos nos primeiros 5 dias úteis
- Respeita feriados nacionais brasileiros (biblioteca `holidays`)
- Alertas: `Caixa normal`, `Atenção: saldo baixo`, `Risco: caixa negativo`

### KPIs Financeiros (20+)

**Receita:** faturamento mensal, MoM, YoY, YTD, média móvel 3M
**Capital de Giro:** AR, AP, Estoque, NCG, PMR, PME, PMP, Ciclo Financeiro
**Endividamento:** Dívida total, por tipo, juros mensais, Debt/Revenue, Cobertura de juros
**Caixa:** Saldo final projetado, menor saldo, dias negativos, necessidade máxima

## Instalação

### Local

```bash
git clone https://github.com/guibiagi/fpa-open-toolkit.git
cd fpa-open-toolkit

# Crie e ative um virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
# .venv\Scripts\activate     # Windows

# Instale o pacote com dependências de dev
pip install -e ".[dev]"
```

### Docker

```bash
docker build -t fpa-open-toolkit .
docker run -p 8000:8000 fpa-open-toolkit
```

## Uso

```bash
make data   # Gera dados sintéticos (data/synthetic/)
make test   # Roda todos os testes (196 atualmente)
make app    # Sobe servidor em http://localhost:8000
make lint   # Verifica formatação com Ruff
```

Ou manualmente:

```bash
# Gerar dados
python -m src.data_generation.synthetic_generator

# Rodar testes
pytest -v --cov=src --cov-report=term-missing

# Iniciar servidor
uvicorn app.main:app --reload --port 8000
```

Acesse http://localhost:8000 para o dashboard ou http://localhost:8000/docs para a documentação OpenAPI.

## Documentação

- [Product Spec](docs/product_spec.md) — especificação completa do MVP
- [Data Dictionary](docs/data_dictionary.md) — dicionário de dados (8 tabelas)
- [Architecture](docs/architecture.md) — decisões de arquitetura e fluxo de dados
- [Roadmap](docs/roadmap.md) — evolução futura (v0.2–v0.6)

## Licença

MIT License — veja [LICENSE](LICENSE) para detalhes.

---

*Projeto open source. Dados sintéticos. Não substitui consultoria financeira profissional.*
