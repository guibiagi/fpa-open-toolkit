# FP&A Open Toolkit

> Análise financeira open source para pequenas e médias empresas industriais.

[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

O **FP&A Open Toolkit** é uma aplicação em Python para simular rotinas de FP&A industrial usando dados sintéticos. Inclui forecast de faturamento, projeção de fluxo de caixa, análise de capital de giro, KPIs financeiros e dashboards via FastAPI + HTMX.

## Documentação

- [Product Spec](docs/product_spec.md) — especificação completa do MVP
- [Data Dictionary](docs/data_dictionary.md) — dicionário de dados
- [Architecture](docs/architecture.md) — decisões de arquitetura
- [Roadmap](docs/roadmap.md) — evolução futura

## Stack

- **Backend:** FastAPI
- **Templates:** Jinja2 + HTMX
- **Gráficos:** Chart.js
- **Estilo:** TailwindCSS
- **Dados:** Pandas
- **Testes:** pytest

## Instalação

```bash
git clone https://github.com/guibiagi/fpa-open-toolkit.git
cd fpa-open-toolkit
pip install -e ".[dev]"
```

## Uso

```bash
make data   # gera dados sintéticos
make test   # roda testes
make app    # sobe o servidor
```

---

*Projeto open source sob licença MIT.*
