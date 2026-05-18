# SPEC DRIVEN DEVELOPMENT
# Projeto: FPA Open Toolkit

> Versão: 1.1-revised  
> Arquitetura: FastAPI + HTMX + Jinja2  
> Licença: MIT  
> Idioma código/docstrings: Inglês | Documentação: PT-BR com abstract EN

---

## 1. Visão Geral

O **FPA Open Toolkit** é uma aplicação open source em Python para auxiliar pequenas e médias empresas industriais a construírem análises financeiras básicas e intermediárias de forma estruturada.

A ferramenta deverá permitir:

- Importar dados financeiros em Excel/CSV.
- Trabalhar com dados sintéticos para demonstração pública.
- Gerar forecast de faturamento.
- Projetar fluxo de caixa.
- Analisar capital de giro.
- Calcular KPIs financeiros.
- Gerar dashboards via interface web.
- Exportar relatórios em Excel.

O projeto deve ser pensado como um portfólio técnico/profissional para GitHub e LinkedIn, demonstrando domínio de:

- Python
- Pandas
- FastAPI
- HTMX
- Jinja2
- Modelagem financeira
- Forecasting
- FP&A
- Organização de código
- Documentação técnica
- Boas práticas de produto open source

---

## 2. Objetivo Principal

Criar uma aplicação open source, didática e funcional, que permita simular uma rotina de FP&A industrial com dados fictícios.

A aplicação não deve depender de dados reais de nenhuma empresa. Todos os dados de demonstração devem ser sintéticos e gerados automaticamente.

---

## 3. Nome do Projeto

Nome escolhido para implementação: **fpa-open-toolkit**

> Nota: FP&A = Financial Planning & Analysis. Não usar grafia "fpna", pois introduz erro permanente.

---

## 4. Público-Alvo

- Analistas financeiros
- Controllers
- CFOs de PMEs
- Consultores financeiros
- Estudantes de finanças
- Profissionais de dados aplicados a negócios
- Empreendedores industriais

---

## 5. Problema que o Projeto Resolve

Muitas PMEs industriais fazem orçamento, forecast e fluxo de caixa em planilhas manuais, com pouca rastreabilidade e baixa padronização.

O projeto resolve isso criando uma base aberta, modular e replicável para:

- Consolidar dados
- Projetar receitas
- Projetar recebimentos
- Projetar pagamentos
- Medir ciclo financeiro
- Visualizar KPIs
- Exportar análises

---

## 6. Escopo do MVP

O MVP deve conter 5 módulos principais:

1. Gerador de dados sintéticos
2. Forecast de faturamento
3. Projeção de fluxo de caixa
4. Cálculo de KPIs financeiros
5. Interface Web (FastAPI + HTMX) com exportação Excel

---

## 7. Módulos do Sistema

### 7.1. Módulo 1 — Synthetic Data Generator

#### Objetivo

Criar dados fictícios realistas para uma PME industrial.

#### Regra Crítica — Determinismo

Todos os datasets devem ser **gerados deterministicamente** quando o mesmo `seed` é fornecido. O seed padrão do projeto é `42`. Isso garante:

- Reprodutibilidade dos exemplos no README
- Testes determinísticos (non-flaky)
- Consistência entre ambientes (dev, CI, demo)

#### Arquivos gerados

O sistema deve gerar arquivos CSV na pasta `data/synthetic/`:

##### 7.1.1. faturamento_historico.csv

Colunas:

- `data_mes`
- `faturamento`
- `canal`
- `familia_produto`

Regras:

- Criar pelo menos 48 meses de histórico.
- Incluir sazonalidade.
- Incluir tendência de crescimento.
- Incluir ruído controlado.
- Incluir famílias de produto.
- Incluir canais comerciais.

##### 7.1.2. contas_receber.csv

Colunas:

- `id_titulo`
- `cliente`
- `data_emissao`
- `data_vencimento`
- `data_pagamento`
- `valor`
- `status`
- `canal`
- `uf`

Status possíveis: `Aberto`, `Recebido`, `Atrasado`

Regras:

- Gerar clientes fictícios.
- Gerar vencimentos com prazos médios entre 30 e 90 dias.
- Simular atrasos.
- Simular inadimplência parcial.
- Simular grandes clientes com maior concentração de receita.

##### 7.1.3. contas_pagar.csv

Colunas:

- `id_titulo`
- `fornecedor`
- `categoria`
- `data_emissao`
- `data_vencimento`
- `data_pagamento`
- `valor`
- `status`

Categorias:

- Matéria-prima
- Embalagem
- Folha
- Impostos
- Frete
- Marketing
- Energia
- Aluguel
- Serviços
- Financeiro

Regras:

- Gerar despesas fixas e variáveis.
- Despesas variáveis devem ter relação parcial com faturamento.
- Matéria-prima deve representar percentual relevante da receita.
- Folha deve ser recorrente.
- Impostos devem seguir datas específicas.
- Financeiro deve simular juros/dívida.

##### 7.1.4. estoque.csv

Colunas:

- `data_mes`
- `categoria`
- `valor_estoque`

Categorias:

- Matéria-prima
- Produto acabado
- Produto em trânsito
- Embalagem

Regras:

- Estoque deve variar conforme faturamento.
- Produto em trânsito deve aparecer para simular importações.
- Deve haver meses com aumento de estoque por lançamento ou compra antecipada.

##### 7.1.5. divida.csv

Colunas:

- `data_mes`
- `tipo_divida`
- `saldo_devedor`
- `juros_mes`
- `amortizacao`
- `prazo_meses`

Tipos:

- Capital de giro
- Financiamento importação
- Investimento produtivo

##### 7.1.6. custo_vendas.csv (NOVO — necessário para PME)

Colunas:

- `data_mes`
- `familia_produto`
- `custo_mes`
- `custo_percentual`

Regras:

- Custo deve variar entre 45% e 65% do faturamento por família.
- Deve conter tendência e sazonalidade.
- Necessário para cálculo do Prazo Médio de Estoque (PME).

---

### 7.2. Módulo 2 — Revenue Forecast

#### Objetivo

Projetar o faturamento mensal futuro com base no histórico.

#### Funcionalidades

- Ler o histórico de faturamento.
- Agregar por mês.
- Gerar forecast para 12 meses (default, parametrizável).
- Criar cenários:
  - Base
  - Otimista
  - Pessimista
- Exibir gráfico do histórico e forecast.
- Exportar forecast.

#### Modelo inicial

Para o MVP, utilizar abordagem simples e interpretável:

- Média móvel dos últimos 3 meses.
- Crescimento médio dos últimos 12 meses.
- Ajuste sazonal por mês do ano (índice de sazonalidade calculado sobre histórico).

Espaço reservado para evolução futura:

- Holt-Winters
- Prophet
- Ridge Regression
- Ensemble

#### Saída esperada

Arquivo: `data/outputs/forecast_faturamento.csv`

Colunas:

- `data_mes`
- `forecast_base`
- `forecast_otimista`
- `forecast_pessimista`

Regras:

- Cenário otimista = base + 10%.
- Cenário pessimista = base - 10%.
- Percentuais devem ser parametrizáveis via interface web.

---

### 7.3. Módulo 3 — Cash Flow Projection

#### Objetivo

Projetar o fluxo de caixa diário dos próximos 90 dias.

#### Inputs

- `contas_receber.csv`
- `contas_pagar.csv`
- `forecast_faturamento.csv`
- Saldo inicial informado pelo usuário via interface web.

#### Funcionalidades

- Calcular entradas previstas.
- Calcular saídas previstas.
- Considerar títulos abertos (contas a receber/a pagar).
- Projetar recebimentos futuros com base no forecast mensal.
- Distribuir forecast mensal em dias úteis de forma **proporcional** (não linear simples).
- Aplicar prazo médio de recebimento para projeções futuras.
- Calcular saldo diário projetado.
- Identificar menor saldo projetado.
- Identificar dias de possível caixa negativo.

#### Regra Crítica — Dias Úteis e Feriados

- Recebimentos e pagamentos devem cair **apenas em dias úteis**.
- Se uma data cair em sábado, domingo ou **feriado nacional brasileiro**, mover para o próximo dia útil.
- Usar biblioteca `holidays` (região BR) para feriados.

#### Saída esperada

Arquivo: `data/outputs/fluxo_caixa_projetado.csv`

Colunas:

- `data`
- `entradas_previstas`
- `saidas_previstas`
- `saldo_inicial_dia`
- `saldo_final_dia`
- `observacao`

Observações possíveis: `Caixa normal`, `Atenção: saldo baixo`, `Risco: caixa negativo`

---

### 7.4. Módulo 4 — Financial KPIs

#### Objetivo

Calcular indicadores financeiros gerenciais a partir dos dados sintéticos.

#### KPIs obrigatórios

##### Receita

- Faturamento mensal.
- Crescimento mensal (MoM).
- Crescimento acumulado no ano (YTD).
- Média móvel de 3 meses.

##### Capital de Giro

- Contas a receber (saldo atual).
- Contas a pagar (saldo atual).
- Estoque (saldo atual).
- Necessidade de capital de giro (NCG).
- Ciclo financeiro aproximado (PMR + PME − PMP).

> Fórmula NCG: Contas a Receber + Estoque − Contas a Pagar

##### Endividamento

- Dívida total.
- Dívida / Receita mensal anualizada.
- Juros pagos no mês.
- Cobertura de juros aproximada (EBITDA estimado / juros).

##### Caixa

- Saldo final projetado.
- Menor saldo projetado.
- Número de dias com caixa negativo.
- Necessidade máxima de caixa.

---

### 7.5. Módulo 5 — Interface Web (FastAPI + HTMX + Jinja2)

#### Objetivo

Criar uma interface web simples, elegante e profissional para visualização e interação com os dados.

#### Arquitetura

- **Backend:** FastAPI (routing, serviço de dados, exportação)
- **Templates:** Jinja2 (herança de templates via `base.html`)
- **Interatividade:** HTMX (atualizações parciais de página sem recarregamento completo)
- **Gráficos:** Chart.js ou ApexCharts via CDN
- **Estilo:** TailwindCSS via CDN (para MVP; build pode vir depois)
- **Estado:** Server-side (formulários POST com parâmetros; nenhum state complexo no cliente)

#### Páginas do app

1. **Overview** (`/`)
2. **Revenue Forecast** (`/forecast`)
3. **Cash Flow** (`/cashflow`)
4. **Working Capital** (`/working-capital`)
5. **Debt** (`/debt`)
6. **Data Explorer** (`/explorer`)

#### Endpoints API (JSON)

Todos os dados dos gráficos devem ser servidos por endpoints REST separados, consumidos via HTMX ou fetch:

- `GET /api/overview` → cards e resumos
- `GET /api/forecast?scenario=base&horizon=12` → dados do forecast
- `GET /api/cashflow?horizon=90&saldo_inicial=0` → dados do fluxo de caixa
- `GET /api/working-capital` → NCG e componentes
- `GET /api/debt` → evolução da dívida
- `GET /api/export/xlsx` → download do relatório completo em Excel

#### Filtros e Query Parameters

Todas as páginas que precisarem de filtro devem usar query parameters nos GET endpoints. Exemplo:

- `/explorer?table=contas_receber&status=Atrasado`
- `/cashflow?scenario=otimista&saldo_inicial=500000`

---

## 8. Página 1 — Overview

### Conteúdo

Exibir cards com:

- Receita últimos 12 meses
- Crescimento YoY
- Saldo de caixa projetado final
- Menor saldo projetado
- Estoque atual
- Dívida total
- Necessidade de capital de giro

### Gráficos

- Receita mensal histórica
- Forecast próximos 12 meses
- Fluxo de caixa diário projetado
- Composição do capital de giro

### Layout

- Cards em grid (2 ou 3 colunas, responsivo).
- Gráficos em cards abaixo.

---

## 9. Página 2 — Revenue Forecast

### Conteúdo

- Gráfico histórico + forecast
- Tabela de forecast
- Seleção de cenário via botões/dropdown
- Campos para ajustar percentuais otimista/pessimista

### Interações

- Botão/radio: Base | Otimista | Pessimista
- Input numérico: horizonte de projeção (1–24 meses)
- Input numérico: percentual otimista (default 10%)
- Input numérico: percentual pessimista (default -10%)
- Aplicar filtros via HTMX (atualização parcial do gráfico e tabela)

---

## 10. Página 3 — Cash Flow

### Conteúdo

- Campo para informar saldo inicial (moeda BRL formatada)
- Gráfico de saldo diário projetado
- Tabela de entradas e saídas (paginada ou últimos 30 dias)
- Alertas de caixa negativo (badge vermelho)
- Destaque: menor saldo projetado

### Interações

- Input: saldo inicial
- Input: horizonte de projeção (30–180 dias)
- Select: cenário de faturamento (base/otimista/pessimista)
- Input: prazo médio de recebimento futuro (dias, default calculado do histórico)
- Botão: reprocessar via HTMX

---

## 11. Página 4 — Working Capital

### Conteúdo

- Cards: Contas a receber, Contas a pagar, Estoque, NCG
- Gráfico de evolução mensal dos componentes
- Gráfico de composição do estoque (pie/donut)
- Tabela: ciclo financeiro (PMR, PME, PMP, ciclo)

### Fórmulas

- NCG = Contas a Receber + Estoque − Contas a Pagar
- Ciclo financeiro = PMR + PME − PMP
- PMR = Prazo médio de recebimento
- PME = Prazo médio de estoque (requer custo de vendas — usar `custo_vendas.csv`)
- PMP = Prazo médio de pagamento

---

## 12. Página 5 — Debt

### Conteúdo

- Dívida total
- Dívida por tipo (stacked bar ou pie)
- Juros mensais
- Amortizações
- Dívida / Receita anualizada
- Gráfico de evolução da dívida

---

## 13. Página 6 — Data Explorer

### Conteúdo

Permitir visualizar as bases disponíveis:

- `faturamento_historico`
- `contas_receber`
- `contas_pagar`
- `estoque`
- `divida`
- `custo_vendas`
- `forecast_faturamento`
- `fluxo_caixa_projetado`

### Interações

- Select para escolher a tabela
- Filtros dinâmicos por coluna: Data, Categoria, Cliente, Fornecedor, Status
- Tabela HTML responsiva com paginação simplificada
- Botão: Exportar visualização atual para Excel

---

## 14. Exportação para Excel

### Requisito

A aplicação deve permitir download de relatório consolidado em `.xlsx` com múltiplas abas:

1. Resumo Executivo
2. Forecast de Receita
3. Fluxo de Caixa Projetado
4. Capital de Giro
5. Endividamento
6. Dados Brutos (todas as tabelas base)

### Implementação

- Usar `openpyxl` ou `xlsxwriter`
- Formatação básica: cabeçalho em negrito, colunas com largura ajustada, números em formato de moeda BRL
- Endpoint: `GET /api/export/xlsx`

---

## 15. Arquitetura do Projeto

Estrutura de pastas esperada:

```text
fpa-open-toolkit/
│
├── pyproject.toml
├── README.md
├── LICENSE (MIT)
├── CONTRIBUTING.md
├── Makefile
├── .gitignore
│
├── data/
│   ├── synthetic/
│   │   ├── faturamento_historico.csv
│   │   ├── contas_receber.csv
│   │   ├── contas_pagar.csv
│   │   ├── estoque.csv
│   │   ├── divida.csv
│   │   └── custo_vendas.csv
│   └── outputs/
│       ├── forecast_faturamento.csv
│       └── fluxo_caixa_projetado.csv
│
├── src/
│   ├── __init__.py
│   ├── data_generation/
│   │   ├── __init__.py
│   │   └── synthetic_generator.py
│   ├── forecasting/
│   │   ├── __init__.py
│   │   └── revenue_forecast.py
│   ├── cashflow/
│   │   ├── __init__.py
│   │   └── cashflow_projection.py
│   ├── kpis/
│   │   ├── __init__.py
│   │   └── financial_kpis.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── dates.py          # dias úteis, feriados BR
│   │   ├── io.py             # leitura/escrita CSV, Excel
│   │   └── formatting.py     # moeda BRL, porcentagem
│   └── export/
│       ├── __init__.py
│       └── xlsx_report.py
│
├── app/
│   ├── __init__.py
│   ├── main.py               # FastAPI app, lifespan
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── pages.py          # rotas HTML (Jinja2)
│   │   ├── api.py            # rotas JSON (dados)
│   │   └── export.py         # download Excel
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html        # Overview
│   │   ├── forecast.html
│   │   ├── cashflow.html
│   │   ├── working_capital.html
│   │   ├── debt.html
│   │   └── explorer.html
│   └── static/
│       ├── css/
│       │   └── custom.css    # mínimo; Tailwind via CDN no base.html
│       └── js/
│           └── charts.js     # helpers Chart.js/ApexCharts
│
├── tests/
│   ├── conftest.py           # fixtures pytest (seed=42)
│   ├── test_synthetic_generator.py
│   ├── test_revenue_forecast.py
│   ├── test_cashflow_projection.py
│   ├── test_financial_kpis.py
│   └── test_dates.py
│
└── docs/
    ├── product_spec.md
    ├── architecture.md
    ├── data_dictionary.md
    └── roadmap.md
```

---

## 16. Stack Tecnológica

| Camada | Tecnologia | Motivo |
|--------|-----------|--------|
| Backend | FastAPI | Performance, tipagem, documentação OpenAPI automática, familiaridade do autor |
| Templates | Jinja2 | Padrão FastAPI, herança de templates, sintaxe limpa |
| Interatividade | HTMX | Atualizações parciais sem SPA complexo, manutenção 100% Python |
| Gráficos | Chart.js (via CDN) | Leve, open source, integra com HTML puro |
| Estilo | TailwindCSS (via CDN) | MVP rápido, customização posterior fácil |
| Dados | Pandas | Padrão em análise financeira |
| Excel | openpyxl | Exportação multi-aba com formatação |
| Feriados | holidays (BR) | Regras oficiais brasileiras, mantido pela comunidade |
| Testes | pytest + cov | Framework padrão Python, fixtures deterministicas |
| Task Runner | Makefile | Comandos padronizados: `make test`, `make data`, `make app`, `make lint` |

---

## 17. Decisões de Engenharia

1. **Determinismo:** `random.seed(42)` obrigatório no generator. CI e demo usam o mesmo seed.
2. **Dias úteis BR:** Sempre usar `pandas.tseries.offsets.BusinessDay` + `holidays.Brazil()`.
3. **PME:** Só é calculável com custo de vendas (COGS). Por isso existe `custo_vendas.csv`.
4. **Moeda:** Todos os valores numéricos armazenados como `float` (unidade: R$). Formatação BRL apenas na camada de apresentação.
5. **Datas:** Sempre usar `YYYY-MM-DD` nos CSVs. Timezone não aplicável (dados mensais/diários sem hora).
6. **Logs:** Usar `logging` do Python. Nível INFO para geração de dados, WARNING para edge cases (ex: caixa negativo).
7. **Configuração:** `pydantic-settings` para variáveis de ambiente (ex: `SEED`, `DATA_DIR`, `OUTPUT_DIR`).

---

## 18. Critérios de Aceite do MVP

- [ ] `make test` passa com 100% dos testes.
- [ ] `make data` gera todos os CSVs sintéticos deterministicamente.
- [ ] `make app` sobe o servidor FastAPI local em `http://localhost:8000`.
- [ ] Todas as 6 páginas renderizam sem erro.
- [ ] Forecast gera 12 meses com cenários Base/Otimista/Pessimista.
- [ ] Cash Flow projeta 90 dias, respeitando sábados, domingos e feriados BR.
- [ ] KPIs calculam NCG e ciclo financeiro com fórmulas corretas.
- [ ] Exportação Excel gera arquivo com 6 abas formatadas.
- [ ] README contém instruções de instalação, badges, GIF de demo e link para app online.
- [ ] Repositório público no GitHub com LICENSE MIT.

---

## 19. Roadmap Pós-MVP

| Fase | Entregável |
|------|-----------|
| v0.2 | Upload de dados reais (Excel/CSV) via interface web |
| v0.3 | Modelos avançados de forecast (Prophet, Holt-Winters) |
| v0.4 | Autenticação simples (usuário/senha) para dados privados |
| v0.5 | Docker Compose com PostgreSQL para persistência |
| v0.6 | Relatórios PDF (WeasyPrint ou Playwright) |

---

*Documento preparado para revisão de implementação.*
