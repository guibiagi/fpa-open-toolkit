# FP&A Open Toolkit

> Análise financeira open source para pequenas e médias empresas industriais.

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/guibiagi/fpa-open-toolkit/actions/workflows/ci.yml/badge.svg)](https://github.com/guibiagi/fpa-open-toolkit/actions)

---

O **FP&A Open Toolkit** é uma aplicação open source em Python para simular e visualizar rotinas de **Financial Planning & Analysis (FP&A)** em uma PME industrial, usando **dados sintéticos**.

Inclui: forecast de faturamento, projeção de fluxo de caixa, análise de capital de giro, cálculo de KPIs financeiros e dashboards interativos via **FastAPI + HTMX + Chart.js**.

> 🚧 *Projeto em construção — dados sintéticos, não substitui consultoria financeira profissional.*

---

## Funcionalidades

| Módulo | Descrição | Status |
|--------|-----------|--------|
| 📊 Gerador de dados sintéticos | 6 datasets realistas para PME industrial (seed=42, determinístico) | ✅ |
| 📈 Forecast de receita | Projeção 12 meses com cenários Base/Otimista/Pessimista | 🟡 |
| 💰 Fluxo de caixa projetado | 90 dias com regras de dias úteis e feriados BR | 🟡 |
| 📐 KPIs financeiros | NCG, ciclo financeiro, endividamento, cobertura de juros | 🟡 |
| 🌐 Dashboard web | FastAPI + HTMX + Chart.js + TailwindCSS | 🟡 |
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
│   ├── data_generation/    # Synthetic data generator
│   ├── forecasting/        # Revenue forecast engine
│   ├── cashflow/           # Cash flow projection engine
│   ├── kpis/               # Financial KPI calculations
│   ├── utils/              # Feriados BR, IO, formatação
│   └── export/             # Exportação Excel
├── app/
│   ├── main.py             # FastAPI app
│   ├── routers/            # Rotas HTML e API
│   ├── templates/          # Jinja2 templates
│   └── static/             # CSS e JS customizados
├── tests/                  # Testes pytest
└── docs/                   # Documentação
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
- **PME** = Prazo Médio de Estoque (dias, requer custo de vendas)
- **PMP** = Prazo Médio de Pagamento (dias)

### Fluxo de Caixa

- Projeção diária por 90 dias
- Distribuição ponderada do forecast mensal em dias úteis
- Títulos abertos (contas a receber/pagar) nas datas de vencimento
- Respeita feriados nacionais brasileiros (biblioteca `holidays`)
- Alertas: caixa normal, atenção (saldo baixo), risco (negativo)

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
make test   # Roda todos os testes
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
- [Data Dictionary](docs/data_dictionary.md) — dicionário de dados
- [Architecture](docs/architecture.md) — decisões de arquitetura
- [Roadmap](docs/roadmap.md) — evolução futura

## Licença

MIT License — veja [LICENSE](LICENSE) para detalhes.

---

*Projeto open source. Dados sintéticos. Não substitui consultoria financeira profissional.*
