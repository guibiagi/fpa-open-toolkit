"""
Synthetic data generator for FP&A Open Toolkit.

Generates 6 deterministic datasets for a fictional Brazilian
pharmaceutical/cosmetic industrial SME. Uses a fixed seed for
reproducibility — same seed always produces identical data.

Usage::

    python -m src.data_generation.synthetic_generator
    # or
    from data_generation.synthetic_generator import generate_all

Spec reference: fpa_open_toolkit_spec_v1.1.md sections 7.1.1–7.1.6
"""

from __future__ import annotations

import datetime
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

DEFAULT_SEED = 42
DEFAULT_DATA_DIR = "data/synthetic"
DEFAULT_OUTPUT_DIR = "data/outputs"

# Product families (pharma/cosmetic industry)
FAMILIAS = ["Higiene", "Diagnóstico", "Dermocosméticos", "Nutracêuticos"]

# Sales channels
CANAIS = ["Distribuidor", "Farma", "Varejo", "E-commerce", "Exportação"]

# Brazilian states (UF)
UFS = ["SP", "RJ", "MG", "RS", "PR", "BA", "PE", "CE", "SC", "GO", "DF", "AM"]

# Expense categories
CATEGORIAS_PAGAR = [
    "Matéria-prima",
    "Embalagem",
    "Folha",
    "Impostos",
    "Frete",
    "Marketing",
    "Energia",
    "Aluguel",
    "Serviços",
    "Financeiro",
]

# Estoque categories
CATEGORIAS_ESTOQUE = [
    "Matéria-prima",
    "Produto acabado",
    "Produto em trânsito",
    "Embalagem",
]

# Debt types
TIPOS_DIVIDA = [
    "Capital de giro",
    "Financiamento importação",
    "Investimento produtivo",
]

# Fixed tax dates (day of month)
TAX_DATES = [15, 20, 25]

# ---------------------------------------------------------------------------
# Random state helper
# ---------------------------------------------------------------------------


def _rng(seed: int) -> np.random.Generator:
    """Create a deterministic random generator from seed."""
    return np.random.default_rng(seed)


# ---------------------------------------------------------------------------
# 7.1.1 — faturamento_historico
# ---------------------------------------------------------------------------


def _generate_faturamento_historico(
    rng: np.random.Generator,
    months: int = 48,
    base_revenue: float = 4_200_000.0,
    growth_rate: float = 0.008,
) -> pd.DataFrame:
    """Generate historical revenue with seasonality, trend, and noise.

    Parameters
    ----------
    months:
        Number of historical months (default: 48).
    base_revenue:
        Starting monthly revenue in BRL.
    growth_rate:
        Monthly growth trend (0.008 = ~10% annual).
    """
    start_date = datetime.date(2022, 1, 1)
    rows: List[Dict[str, Any]] = []

    for i in range(months):
        current_date = _add_months(start_date, i)
        month = current_date.month

        # Seasonality index — Dec is peak, Jan is trough
        seasonal_idx = _seasonality(month)

        # Trend component
        trend = (1 + growth_rate) ** i

        # Random noise (±5%)
        noise = 1.0 + rng.uniform(-0.05, 0.05)

        base = base_revenue * seasonal_idx * trend * noise

        # Generate one row per family × channel combination
        family_weights = {
            "Higiene": 0.35,
            "Diagnóstico": 0.25,
            "Dermocosméticos": 0.25,
            "Nutracêuticos": 0.15,
        }
        channel_weights = {
            "Distribuidor": 0.40,
            "Farma": 0.30,
            "Varejo": 0.15,
            "E-commerce": 0.10,
            "Exportação": 0.05,
        }

        for familia, fw in family_weights.items():
            for canal, cw in channel_weights.items():
                # Apply slight per-family per-channel variation
                variation = rng.uniform(0.85, 1.15)
                revenue = base * fw * cw * variation
                rows.append(
                    {
                        "data_mes": current_date.isoformat(),
                        "faturamento": round(revenue, 2),
                        "canal": canal,
                        "familia_produto": familia,
                    }
                )

    df = pd.DataFrame(rows)
    df["data_mes"] = pd.to_datetime(df["data_mes"])
    return df.sort_values(["data_mes", "familia_produto", "canal"]).reset_index(
        drop=True
    )


# ---------------------------------------------------------------------------
# 7.1.2 — contas_receber
# ---------------------------------------------------------------------------


def _generate_contas_receber(
    rng: np.random.Generator,
    faturamento_df: pd.DataFrame,
) -> pd.DataFrame:
    """Generate accounts receivable with realistic aging and defaults."""
    # Aggregate revenue per month for scaling
    monthly = faturamento_df.groupby("data_mes")["faturamento"].sum().reset_index()

    # Generate fictional clients with Pareto distribution
    n_clients = 40
    clientes = [f"Cliente {chr(65 + i % 26)}{i + 1:02d}" for i in range(n_clients)]
    # Pareto: few large clients, many small
    pareto_weights = np.sort(rng.exponential(scale=1.0, size=n_clients))[::-1]
    pareto_weights /= pareto_weights.sum()

    rows: List[Dict[str, Any]] = []
    titulo_id = 0

    for _, row in monthly.iterrows():
        data_emissao_base = row["data_mes"].date()  # pd.Timestamp → datetime.date
        month_revenue = row["faturamento"]        # Each month generates ~15-30 titles
        n_titulos = rng.integers(15, 31)

        # Distribute monthly revenue across titles with Pareto client weights
        for _ in range(n_titulos):
            titulo_id += 1
            cliente = rng.choice(clientes, p=pareto_weights)

            # Emission date: spread across the month
            day = rng.integers(1, 28)  # Safe day for all months
            try:
                data_emissao = data_emissao_base.replace(day=int(day))
            except ValueError:
                data_emissao = data_emissao_base.replace(day=28)

            # Due date: 30 to 90 days after emission
            prazo = rng.integers(30, 91)
            data_vencimento = data_emissao + datetime.timedelta(days=int(prazo))

            # Value: Pareto-distributed fraction of month revenue
            frac = rng.exponential(scale=0.03)
            valor = round(month_revenue * min(frac, 0.30), 2)

            # Payment status
            hoje = datetime.date(2026, 5, 24)
            status = _determine_ar_status(
                rng, data_vencimento, hoje
            )
            data_pagamento: Optional[datetime.date] = None
            if status == "Recebido":
                # Paid on time or slightly early
                data_pagamento = data_vencimento - datetime.timedelta(
                    days=int(rng.integers(0, 5))
                )
            elif status == "Atrasado":
                # Not paid yet (past due)
                data_pagamento = None

            rows.append(
                {
                    "id_titulo": f"AR-{titulo_id:06d}",
                    "cliente": cliente,
                    "data_emissao": data_emissao.isoformat(),
                    "data_vencimento": data_vencimento.isoformat(),
                    "data_pagamento": (
                        data_pagamento.isoformat() if data_pagamento else None
                    ),
                    "valor": max(valor, 100.0),  # minimum BRL 100
                    "status": status,
                    "canal": rng.choice(CANAIS),
                    "uf": rng.choice(UFS),
                }
            )

    df = pd.DataFrame(rows)
    for col in ["data_emissao", "data_vencimento", "data_pagamento"]:
        df[col] = pd.to_datetime(df[col])
    return df.sort_values("data_emissao").reset_index(drop=True)


def _determine_ar_status(
    rng: np.random.Generator,
    due_date: Any,
    hoje: datetime.date,
) -> str:
    """Determine if a receivable is Aberto, Recebido, or Atrasado."""
    # Normalize to date for comparison (may be pd.Timestamp or datetime.date)
    d = due_date.date() if hasattr(due_date, "date") else due_date
    if d > hoje:
        return "Aberto"
    elif d <= hoje:
        # 70% chance paid, 20% late/atrasado, 10% open (waiting)
        p = rng.random()
        if p < 0.70:
            return "Recebido"
        elif p < 0.90:
            return "Atrasado"
        else:
            return "Aberto"
    return "Aberto"


# ---------------------------------------------------------------------------
# 7.1.3 — contas_pagar
# ---------------------------------------------------------------------------


def _generate_contas_pagar(
    rng: np.random.Generator,
    faturamento_df: pd.DataFrame,
) -> pd.DataFrame:
    """Generate accounts payable with fixed and variable expenses."""
    monthly = faturamento_df.groupby("data_mes")["faturamento"].sum().reset_index()

    # Supplier names per category
    fornecedores_map = {
        "Matéria-prima": ["Química Brasil Ltda", "Insumos Farmacêuticos SA",
                          "BioAtivos Indústria", "Nacional Matérias-Primas"],
        "Embalagem": ["PackMaster Embalagens", "FlexPrint Indústria", "VidroBrasil Ltda"],
        "Folha": ["Folha de Pagamento"],
        "Impostos": ["Receita Federal", "SEFAZ-SP"],
        "Frete": ["Transportadora RápidoLog", "Expresso Sudeste", "CargaPesada Ltda"],
        "Marketing": ["Agência Criativa", "Mídia Digital Brasil"],
        "Energia": ["CPFL Energia", "Concessionária Local"],
        "Aluguel": ["Imobiliária Central", "Galpão Industrial Locação"],
        "Serviços": ["TI Solutions", "Limpeza Profissional", "Segurança 24h"],
        "Financeiro": ["Banco Santander", "Bradesco", "Itaú"],
    }

    # Category type: "fixed" or "variable"
    category_type = {
        "Matéria-prima": "variable",
        "Embalagem": "variable",
        "Folha": "fixed",
        "Impostos": "fixed",
        "Frete": "variable",
        "Marketing": "fixed",
        "Energia": "fixed",
        "Aluguel": "fixed",
        "Serviços": "fixed",
        "Financeiro": "fixed",
    }

    rows: List[Dict[str, Any]] = []
    titulo_id = 0

    for _, row in monthly.iterrows():
        data_emissao_base = row["data_mes"].date()  # pd.Timestamp → datetime.date
        month_revenue = row["faturamento"]
        for categoria in CATEGORIAS_PAGAR:
            fornecedores = fornecedores_map[categoria]
            fornecedor = rng.choice(fornecedores)

            # Calculate base value
            if category_type[categoria] == "fixed":
                base_val = _fixed_expense(categoria, rng)
            else:
                base_val = _variable_expense(categoria, month_revenue, rng)

            # Generate 1-3 titles per category per month
            n_titulos = rng.integers(1, 4)
            for _ in range(n_titulos):
                titulo_id += 1
                day = rng.integers(1, 28)
                try:
                    data_emissao = data_emissao_base.replace(day=int(day))
                except ValueError:
                    data_emissao = data_emissao_base.replace(day=28)

                # Due date: 15-60 days for variable, specific for fixed
                if categoria == "Impostos":
                    # Taxes fall on specific days
                    tax_day = int(rng.choice(TAX_DATES))
                    data_vencimento = data_emissao_base.replace(day=min(tax_day, 28))
                    if data_vencimento <= data_emissao:
                        data_vencimento = _add_months(data_vencimento, 1)
                else:
                    prazo = rng.integers(15, 61)
                    data_vencimento = data_emissao + datetime.timedelta(days=int(prazo))

                valor = round(base_val / n_titulos * rng.uniform(0.7, 1.3), 2)

                # Payment status
                hoje = datetime.date(2026, 5, 24)
                if data_vencimento > hoje:
                    status = "Aberto"
                elif data_vencimento <= hoje and rng.random() < 0.85:
                    status = "Pago"
                else:
                    status = "Aberto"

                data_pagamento: Optional[str] = None
                if status == "Pago":
                    paid_date = data_vencimento - datetime.timedelta(
                        days=int(rng.integers(0, 3))
                    )
                    data_pagamento = paid_date.isoformat()

                rows.append(
                    {
                        "id_titulo": f"AP-{titulo_id:06d}",
                        "fornecedor": fornecedor,
                        "categoria": categoria,
                        "data_emissao": data_emissao.isoformat(),
                        "data_vencimento": data_vencimento.isoformat(),
                        "data_pagamento": data_pagamento,
                        "valor": max(valor, 50.0),
                        "status": status,
                    }
                )

    df = pd.DataFrame(rows)
    for col in ["data_emissao", "data_vencimento", "data_pagamento"]:
        df[col] = pd.to_datetime(df[col])
    return df.sort_values("data_emissao").reset_index(drop=True)


def _fixed_expense(categoria: str, rng: np.random.Generator) -> float:
    """Return base monthly fixed expense for a category."""
    bases = {
        "Folha": 380_000,
        "Impostos": 120_000,
        "Marketing": 45_000,
        "Energia": 28_000,
        "Aluguel": 35_000,
        "Serviços": 55_000,
        "Financeiro": 18_000,
    }
    base = bases.get(categoria, 30_000)
    return base * rng.uniform(0.85, 1.15)


def _variable_expense(
    categoria: str, revenue: float, rng: np.random.Generator
) -> float:
    """Return base monthly variable expense for a category."""
    rates = {
        "Matéria-prima": 0.35,
        "Embalagem": 0.06,
        "Frete": 0.04,
    }
    rate = rates.get(categoria, 0.03)
    return revenue * rate * rng.uniform(0.85, 1.15)


# ---------------------------------------------------------------------------
# 7.1.4 — estoque
# ---------------------------------------------------------------------------


def _generate_estoque(
    rng: np.random.Generator,
    faturamento_df: pd.DataFrame,
) -> pd.DataFrame:
    """Generate inventory data that varies with revenue."""
    monthly = faturamento_df.groupby("data_mes")["faturamento"].sum().reset_index()

    # Inventory-to-revenue ratios per category
    ratios = {
        "Matéria-prima": (0.25, 0.35),
        "Produto acabado": (0.20, 0.30),
        "Produto em trânsito": (0.05, 0.12),
        "Embalagem": (0.04, 0.08),
    }

    rows: List[Dict[str, Any]] = []
    for _, row in monthly.iterrows():
        data_mes = row["data_mes"]
        revenue = row["faturamento"]

        for categoria, (lo, hi) in ratios.items():
            # Inventory = ratio × monthly revenue + noise
            ratio = rng.uniform(lo, hi)
            valor = revenue * ratio * rng.uniform(0.90, 1.10)

            # Occasionally spike inventory (stock build-up)
            if rng.random() < 0.10:
                valor *= rng.uniform(1.15, 1.35)

            rows.append(
                {
                    "data_mes": data_mes.isoformat(),
                    "categoria": categoria,
                    "valor_estoque": round(valor, 2),
                }
            )

    df = pd.DataFrame(rows)
    df["data_mes"] = pd.to_datetime(df["data_mes"])
    return df.sort_values(["data_mes", "categoria"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# 7.1.5 — divida
# ---------------------------------------------------------------------------


def _generate_divida(
    rng: np.random.Generator,
    months: int = 48,
) -> pd.DataFrame:
    """Generate debt evolution over time."""
    start_date = datetime.date(2022, 1, 1)

    # Initial debt per type
    initial_debt = {
        "Capital de giro": 2_500_000.0,
        "Financiamento importação": 1_800_000.0,
        "Investimento produtivo": 4_200_000.0,
    }
    prazo_meses = {
        "Capital de giro": 24,
        "Financiamento importação": 36,
        "Investimento produtivo": 60,
    }
    juros_anual = {
        "Capital de giro": 0.18,
        "Financiamento importação": 0.12,
        "Investimento produtivo": 0.09,
    }

    rows: List[Dict[str, Any]] = []
    for tipo in TIPOS_DIVIDA:
        saldo = initial_debt[tipo]
        prazo = prazo_meses[tipo]
        juros_mensal = juros_anual[tipo] / 12
        amortizacao_mensal = initial_debt[tipo] / prazo

        for i in range(months):
            current_date = _add_months(start_date, i)

            # Interest on current balance
            juros = round(saldo * juros_mensal * rng.uniform(0.95, 1.05), 2)

            # Amortization with slight variation
            amort = round(amortizacao_mensal * rng.uniform(0.90, 1.10), 2)
            amort = min(amort, saldo)  # Don't amortize more than balance

            saldo = max(round(saldo - amort, 2), 0.0)

            rows.append(
                {
                    "data_mes": current_date.isoformat(),
                    "tipo_divida": tipo,
                    "saldo_devedor": saldo,
                    "juros_mes": juros,
                    "amortizacao": amort,
                    "prazo_meses": prazo - min(i, prazo),
                }
            )

    df = pd.DataFrame(rows)
    df["data_mes"] = pd.to_datetime(df["data_mes"])
    return df.sort_values(["data_mes", "tipo_divida"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# 7.1.6 — custo_vendas
# ---------------------------------------------------------------------------


def _generate_custo_vendas(
    rng: np.random.Generator,
    faturamento_df: pd.DataFrame,
) -> pd.DataFrame:
    """Generate cost of goods sold per product family.

    Spec: 45-65% of revenue, varying by family.
    """
    monthly = (
        faturamento_df.groupby(["data_mes", "familia_produto"])["faturamento"]
        .sum()
        .reset_index()
    )

    # Base cost percentages per family
    cost_pcts = {
        "Higiene": (0.46, 0.55),
        "Diagnóstico": (0.50, 0.60),
        "Dermocosméticos": (0.52, 0.62),
        "Nutracêuticos": (0.48, 0.58),
    }

    rows: List[Dict[str, Any]] = []
    for _, row in monthly.iterrows():
        familia = row["familia_produto"]
        lo, hi = cost_pcts.get(str(familia), (0.45, 0.65))
        pct = rng.uniform(lo, hi)
        custo = round(row["faturamento"] * pct, 2)

        rows.append(
            {
                "data_mes": row["data_mes"].isoformat(),
                "familia_produto": familia,
                "custo_mes": custo,
                "custo_percentual": round(pct, 4),
            }
        )

    df = pd.DataFrame(rows)
    df["data_mes"] = pd.to_datetime(df["data_mes"])
    return df.sort_values(["data_mes", "familia_produto"]).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _seasonality(month: int) -> float:
    """Return a seasonality multiplier for a given month (1-12).

    December is peak (Xmas/New Year orders), January is trough.
    """
    indices = {
        1: 0.82,
        2: 0.88,
        3: 0.95,
        4: 0.97,
        5: 1.02,
        6: 1.00,
        7: 1.00,
        8: 1.03,
        9: 1.05,
        10: 1.08,
        11: 1.10,
        12: 1.15,
    }
    return indices.get(month, 1.0)


def _add_months(dt: datetime.date, n: int) -> datetime.date:
    """Add n months to a date, clamping to month-end if needed."""
    month = dt.month - 1 + n
    year = dt.year + month // 12
    month = month % 12 + 1
    day = min(dt.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
    return datetime.date(year, month, day)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_all(
    seed: int = DEFAULT_SEED,
    output_dir: Optional[str] = None,
) -> Dict[str, pd.DataFrame]:
    """Generate all 6 synthetic datasets and optionally write to CSV.

    Parameters
    ----------
    seed:
        Random seed for reproducibility (default: 42).
    output_dir:
        If provided, write CSVs to this directory.
        Creates the directory if it doesn't exist.

    Returns
    -------
    dict[str, pd.DataFrame]
        Mapping of dataset name to DataFrame.
        Keys: faturamento_historico, contas_receber, contas_pagar,
              estoque, divida, custo_vendas
    """
    rng = _rng(seed)

    # 7.1.1 — Must come first as others depend on it
    faturamento = _generate_faturamento_historico(rng)

    # 7.1.2–7.1.6
    datasets: Dict[str, pd.DataFrame] = {
        "faturamento_historico": faturamento,
        "contas_receber": _generate_contas_receber(rng, faturamento),
        "contas_pagar": _generate_contas_pagar(rng, faturamento),
        "estoque": _generate_estoque(rng, faturamento),
        "divida": _generate_divida(rng),
        "custo_vendas": _generate_custo_vendas(rng, faturamento),
    }

    # Write CSVs if output_dir specified
    if output_dir:
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        for name, df in datasets.items():
            csv_path = out_path / f"{name}.csv"
            df.to_csv(csv_path, index=False)

    return datasets


def main() -> None:
    """Entry point for ``python -m src.data_generation.synthetic_generator``."""
    print(f"FP&A Open Toolkit — Synthetic Data Generator (seed={DEFAULT_SEED})")
    datasets = generate_all(seed=DEFAULT_SEED, output_dir=DEFAULT_DATA_DIR)

    for name, df in datasets.items():
        print(f"  ✅ {name}.csv — {len(df):,} rows, {len(df.columns)} cols")

    print(f"\nAll 6 datasets written to {DEFAULT_DATA_DIR}/")


if __name__ == "__main__":
    main()
