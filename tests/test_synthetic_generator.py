"""Tests for :mod:`data_generation.synthetic_generator`.

These tests validate the synthetic data generator against the project spec
(``fpa_open_toolkit_spec_v1.1.md`` sections 7.1.1–7.1.6).

All tests are skipped until the generator is implemented (issue #3).
Once #3 is complete, run::

    pytest tests/test_synthetic_generator.py -v
"""

from __future__ import annotations

import datetime
from pathlib import Path

import pandas as pd
import pytest

# ---------------------------------------------------------------------------
# Module-level guard — skip everything until the generator module exists.
# Remove the ``pytest.importorskip`` call after issue #3 is merged.
# ---------------------------------------------------------------------------
synthetic_generator = pytest.importorskip("data_generation.synthetic_generator")


# ── helpers ────────────────────────────────────────────────────────────────


def _generate(seed: int = 42) -> dict[str, pd.DataFrame]:
    """Call the generator and return a dict of {name: DataFrame}.

    Assumes the generator exposes a ``generate_all(seed=..., output_dir=...)``
    that returns ``dict[str, pd.DataFrame]``.
    """
    return synthetic_generator.generate_all(seed=seed, output_dir="data/synthetic/")


# ── determinism ────────────────────────────────────────────────────────────


class TestDeterminism:
    """Generator must be deterministic when the same seed is used."""

    def test_same_seed_produces_identical_data(self) -> None:
        """Two calls with seed=42 should return equal DataFrames."""
        run1 = _generate(seed=42)
        run2 = _generate(seed=42)

        assert set(run1.keys()) == set(run2.keys()), (
            f"Keys differ: {set(run1.keys())} vs {set(run2.keys())}"
        )

        for name, df1 in run1.items():
            df2 = run2[name]
            pd.testing.assert_frame_equal(df1, df2, obj=f"dataset={name}")

    def test_different_seeds_produce_different_data(self) -> None:
        """Two calls with different seeds should produce different DataFrames."""
        run1 = _generate(seed=42)
        run2 = _generate(seed=123)

        for name, df1 in run1.items():
            df2 = run2[name]
            if not df1.empty and not df2.empty and set(df1.columns) == set(df2.columns):
                # At least one numeric column should differ.
                numeric_cols = df1.select_dtypes(include="number").columns
                if len(numeric_cols) > 0:
                    assert not df1[numeric_cols].equals(df2[numeric_cols]), (
                        f"dataset={name} is identical despite different seeds"
                    )


# ── schema ─────────────────────────────────────────────────────────────────


EXPECTED_SCHEMAS = {
    "faturamento_historico": {"data_mes", "faturamento", "canal", "familia_produto"},
    "contas_receber": {
        "id_titulo", "cliente", "data_emissao", "data_vencimento",
        "data_pagamento", "valor", "status", "canal", "uf",
    },
    "contas_pagar": {
        "id_titulo", "fornecedor", "categoria", "data_emissao",
        "data_vencimento", "data_pagamento", "valor", "status",
    },
    "estoque": {"data_mes", "categoria", "valor_estoque"},
    "divida": {
        "data_mes", "tipo_divida", "saldo_devedor", "juros_mes",
        "amortizacao", "prazo_meses",
    },
    "custo_vendas": {
        "data_mes", "familia_produto", "custo_mes", "custo_percentual",
    },
}


class TestSchema:
    """Each generated CSV must contain the columns defined in the spec."""

    @pytest.mark.parametrize("name,expected_cols", EXPECTED_SCHEMAS.items())
    def test_columns_match_spec(self, name: str, expected_cols: set[str]) -> None:
        data = _generate(seed=42)
        assert name in data, f"Dataset '{name}' not found in generator output"
        df = data[name]
        actual_cols = set(df.columns)
        missing = expected_cols - actual_cols
        extra = actual_cols - expected_cols
        assert not missing, f"{name}: missing columns {missing}"
        # Extra columns are allowed (generator may include helpers).
        assert expected_cols.issubset(actual_cols), (
            f"{name}: expected {expected_cols}, got {actual_cols}"
        )

    def test_faturamento_historico_has_48_months(self) -> None:
        """Spec §7.1.1: at least 48 months of history."""
        data = _generate(seed=42)
        df = data["faturamento_historico"]
        assert "data_mes" in df.columns
        unique_months = df["data_mes"].nunique()
        assert unique_months >= 48, (
            f"Expected ≥48 months, got {unique_months}"
        )

    def test_contas_receber_status_values(self) -> None:
        """Spec §7.1.2: status must be one of Aberto, Recebido, Atrasado."""
        data = _generate(seed=42)
        df = data["contas_receber"]
        valid_status = {"Aberto", "Recebido", "Atrasado"}
        actual = set(df["status"].unique())
        invalid = actual - valid_status
        assert not invalid, f"Invalid status values: {invalid}"

    def test_contas_pagar_categories(self) -> None:
        """Spec §7.1.3: categories must be from the canonical set."""
        data = _generate(seed=42)
        df = data["contas_pagar"]
        valid_categories = {
            "Matéria-prima", "Embalagem", "Folha", "Impostos",
            "Frete", "Marketing", "Energia", "Aluguel",
            "Serviços", "Financeiro",
        }
        actual = set(df["categoria"].unique())
        invalid = actual - valid_categories
        assert not invalid, f"Invalid categories: {invalid}"

    def test_estoque_categories(self) -> None:
        """Spec §7.1.4: estoque categories."""
        data = _generate(seed=42)
        df = data["estoque"]
        valid = {
            "Matéria-prima", "Produto acabado",
            "Produto em trânsito", "Embalagem",
        }
        actual = set(df["categoria"].unique())
        invalid = actual - valid
        assert not invalid, f"Invalid estoque categories: {invalid}"

    def test_divida_types(self) -> None:
        """Spec §7.1.5: dívida types."""
        data = _generate(seed=42)
        df = data["divida"]
        valid = {"Capital de giro", "Financiamento importação", "Investimento produtivo"}
        actual = set(df["tipo_divida"].unique())
        invalid = actual - valid
        assert not invalid, f"Invalid dívida types: {invalid}"


# ── ranges ─────────────────────────────────────────────────────────────────


class TestRanges:
    """Values must fall within reasonable ranges per the spec."""

    def test_faturamento_positive(self) -> None:
        """Spec §7.1.1: faturamento > 0."""
        data = _generate(seed=42)
        df = data["faturamento_historico"]
        assert (df["faturamento"] > 0).all(), "Found non-positive faturamento"

    def test_contas_receber_prazos(self) -> None:
        """Spec §7.1.2: prazos médios entre 30 e 90 dias."""
        data = _generate(seed=42)
        df = data["contas_receber"]
        # Ensure date columns are datetime
        emissao = pd.to_datetime(df["data_emissao"])
        vencimento = pd.to_datetime(df["data_vencimento"])
        prazo = (vencimento - emissao).dt.days
        # At least some titles should fall in 30–90 range.
        in_range = prazo.between(30, 90)
        assert in_range.any(), (
            f"No titles with prazo 30-90 days. Range: {prazo.min()}-{prazo.max()}"
        )

    def test_custo_vendas_percentual_range(self) -> None:
        """Spec §7.1.6: custo between 45% and 65% of faturamento."""
        data = _generate(seed=42)
        df = data["custo_vendas"]
        assert "custo_percentual" in df.columns
        pct = df["custo_percentual"]
        # Allow small floating-point margin.
        assert pct.min() >= 0.44, f"Min cost percentage {pct.min()} < 44%"
        assert pct.max() <= 0.66, f"Max cost percentage {pct.max()} > 66%"

    def test_estoque_values_positive(self) -> None:
        """Estoque values must be positive."""
        data = _generate(seed=42)
        df = data["estoque"]
        assert (df["valor_estoque"] > 0).all(), "Found non-positive estoque"


# ── sanity ─────────────────────────────────────────────────────────────────


class TestSanity:
    """Cross-dataset coherence checks."""

    def test_contas_receber_not_exceeds_faturamento(self) -> None:
        """Total contas a receber should not greatly exceed total faturamento."""
        data = _generate(seed=42)
        receber = data["contas_receber"]
        fat = data["faturamento_historico"]

        total_receber = receber["valor"].sum()
        total_faturamento = fat["faturamento"].sum()

        # Accounts receivable may be ≤ 2× total revenue (for rolling balances).
        # If it exceeds this, something is likely wrong.
        assert total_receber <= total_faturamento * 2, (
            f"contas_receber ({total_receber:,.2f}) > 2× faturamento ({total_faturamento:,.2f})"
        )

    def test_custo_familias_match_faturamento(self) -> None:
        """Spec §7.1.6: custo_vendas families must match faturamento families."""
        data = _generate(seed=42)
        fat_familias = set(data["faturamento_historico"]["familia_produto"].unique())
        custo_familias = set(data["custo_vendas"]["familia_produto"].unique())
        if custo_familias:  # Only check if non-empty
            missing = custo_familias - fat_familias
            assert not missing, (
                f"custo_vendas has families not in faturamento: {missing}"
            )


# ── completeness ───────────────────────────────────────────────────────────


class TestCompleteness:
    """Ensure the generator produces all required datasets."""

    def test_all_six_datasets_generated(self) -> None:
        """Spec requires exactly 6 synthetic datasets."""
        data = _generate(seed=42)
        expected = {
            "faturamento_historico", "contas_receber", "contas_pagar",
            "estoque", "divida", "custo_vendas",
        }
        actual = set(data.keys())
        missing = expected - actual
        assert not missing, f"Missing datasets: {missing}"

    def test_no_empty_dataframes(self) -> None:
        """No generated dataset should be empty."""
        data = _generate(seed=42)
        for name, df in data.items():
            assert not df.empty, f"Dataset '{name}' is empty"
            assert len(df) > 0, f"Dataset '{name}' has 0 rows"
