# Dicionário de Dados

## Datasets Sintéticos (Input)

Gerados deterministicamente por `src/data_generation/synthetic_generator.py` (seed=42).

### 1. faturamento_historico.csv

Histórico mensal de faturamento por família de produto e canal.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `data_mes` | date (YYYY-MM-DD) | Primeiro dia do mês de referência |
| `faturamento` | float | Faturamento bruto do mês (R$) |
| `canal` | string | Canal de venda (Distribuidor, Farma, Varejo, E-commerce, Exportação) |
| `familia_produto` | string | Família do produto (Higiene, Diagnóstico, Dermocosméticos, Nutracêuticos) |

**Regras:** 48 meses de histórico, sazonalidade, tendência de crescimento, ruído controlado.
**Consumido por:** `revenue_forecast.py`, `financial_kpis.py`

---

### 2. contas_receber.csv

Títulos a receber (duplicatas, vendas a prazo).

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id_titulo` | string | Identificador único do título |
| `cliente` | string | Nome do cliente |
| `data_emissao` | date (YYYY-MM-DD) | Data de emissão do título |
| `data_vencimento` | date (YYYY-MM-DD) | Data de vencimento |
| `data_pagamento` | date (YYYY-MM-DD) ou NaN | Data efetiva de pagamento (se recebido) |
| `valor` | float | Valor do título (R$) |
| `status` | string | Aberto, Recebido, Atrasado |
| `canal` | string | Canal de venda |
| `uf` | string | Unidade federativa do cliente |

**Regras:** Prazos 30-90 dias, concentração Pareto 80/20, inadimplência parcial.
**Consumido por:** `cashflow_projection.py`, `financial_kpis.py`

---

### 3. contas_pagar.csv

Títulos a pagar (fornecedores, despesas).

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `id_titulo` | string | Identificador único do título |
| `fornecedor` | string | Nome do fornecedor |
| `categoria` | string | Categoria da despesa |
| `data_emissao` | date (YYYY-MM-DD) | Data de emissão |
| `data_vencimento` | date (YYYY-MM-DD) | Data de vencimento |
| `data_pagamento` | date (YYYY-MM-DD) ou NaN | Data efetiva de pagamento (se pago) |
| `valor` | float | Valor do título (R$) |
| `status` | string | Aberto, Pago, Atrasado |

**Categorias:** Matéria-prima, Embalagem, Folha, Impostos, Frete, Marketing, Energia, Aluguel, Serviços, Financeiro.
**Regras:** Despesas fixas e variáveis. Matéria-prima = 30-40% da receita. Impostos em datas fixas.
**Consumido por:** `cashflow_projection.py`, `financial_kpis.py`

---

### 4. estoque.csv

Saldo de estoque mensal por categoria.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `data_mes` | date (YYYY-MM-DD) | Primeiro dia do mês de referência |
| `categoria` | string | Categoria do estoque |
| `valor_estoque` | float | Valor do estoque (R$) |

**Categorias:** Matéria-prima, Produto acabado, Produto em trânsito, Embalagem.
**Regras:** Varia conforme faturamento. Inclui meses com aumento por compra antecipada.
**Consumido por:** `financial_kpis.py`

---

### 5. divida.csv

Evolução mensal da dívida por tipo.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `data_mes` | date (YYYY-MM-DD) | Primeiro dia do mês de referência |
| `tipo_divida` | string | Tipo de dívida |
| `saldo_devedor` | float | Saldo devedor no mês (R$) |
| `juros_mes` | float | Juros pagos no mês (R$) |
| `amortizacao` | float | Amortização no mês (R$) |
| `prazo_meses` | int | Prazo original em meses |

**Tipos:** Capital de giro, Financiamento importação, Investimento produtivo.
**Consumido por:** `financial_kpis.py`

---

### 6. custo_vendas.csv

Custo mensal de vendas (COGS) por família de produto.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `data_mes` | date (YYYY-MM-DD) | Primeiro dia do mês de referência |
| `familia_produto` | string | Família do produto |
| `custo_mes` | float | Custo do mês (R$) |
| `custo_percentual` | float | Custo como % do faturamento da família |

**Regras:** 45-65% do faturamento, tendência e sazonalidade. Necessário para PME.
**Consumido por:** `financial_kpis.py` (cálculo do PME)

---

## Datasets de Output (Engines)

### 7. forecast_faturamento.csv

Projeção mensal de faturamento futuro. Gerado por `src/forecasting/revenue_forecast.py`.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `data_mes` | date (YYYY-MM-DD) | Primeiro dia do mês projetado |
| `forecast_base` | float | Cenário base (R$) |
| `forecast_otimista` | float | Cenário otimista = base + 10% (R$) |
| `forecast_pessimista` | float | Cenário pessimista = base − 10% (R$) |

**Horizonte default:** 12 meses (máx 24). Percentuais parametrizáveis.

### 8. fluxo_caixa_projetado.csv

Projeção diária de fluxo de caixa para 90 dias. Gerado por `src/cashflow/cashflow_projection.py`.

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `data` | date (YYYY-MM-DD) | Data do dia projetado |
| `entradas_previstas` | float | Total de entradas do dia (R$) |
| `saidas_previstas` | float | Total de saídas do dia (R$) |
| `saldo_inicial_dia` | float | Saldo no início do dia (R$) |
| `saldo_final_dia` | float | Saldo ao final do dia (R$) |
| `observacao` | string | Classificação do risco: `Caixa normal`, `Atenção: saldo baixo`, `Risco: caixa negativo` |

**Horizonte default:** 90 dias corridos. Saldo inicial parametrizável.

---

*Nota: Datas no formato ISO 8601 (`YYYY-MM-DD`). Valores monetários em R$ (float). Dados 100% sintéticos — sem informações reais de empresas.*
