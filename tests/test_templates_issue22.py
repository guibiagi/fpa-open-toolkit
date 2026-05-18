"""Tests for Data Explorer template and static assets — Issue #22.

- app/templates/explorer.html
- app/static/css/custom.css
- app/static/js/charts.js
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, select_autoescape


# ── Fixtures ───────────────────────────────────────────────

@pytest.fixture
def project_root() -> Path:
    return Path(__file__).parent.parent


@pytest.fixture
def env(project_root: Path) -> Environment:
    templates_dir = project_root / "app" / "templates"
    return Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


@pytest.fixture
def css_content(project_root: Path) -> str:
    return (project_root / "app" / "static" / "css" / "custom.css").read_text()


@pytest.fixture
def js_content(project_root: Path) -> str:
    return (project_root / "app" / "static" / "js" / "charts.js").read_text()


class MockRequest:
    class MockURL:
        def __init__(self, path: str):
            self.path = path
    def __init__(self, path: str = "/"):
        self.url = self.MockURL(path)


def render(template_name: str, env: Environment, **ctx) -> str:
    template = env.get_template(template_name)
    defaults = {"request": MockRequest("/explorer")}
    defaults.update(ctx)
    return template.render(**defaults)


# ── Explorer Template Tests ────────────────────────────────

class TestExplorerTemplate:
    """Tests for explorer.html — Data Explorer page."""

    def test_renders_without_error(self, env: Environment):
        html = render("explorer.html", env)
        assert html.strip()

    def test_extends_base(self, env: Environment):
        template = env.get_template("explorer.html")
        source = template.render(request=MockRequest("/explorer"))
        assert "Data Explorer" in source

    def test_contains_table_select_with_8_options(self, env: Environment):
        html = render("explorer.html", env)
        assert 'name="table"' in html
        assert "Faturamento Histórico" in html
        assert "Contas a Receber" in html
        assert "Contas a Pagar" in html
        assert "Estoque" in html
        assert "Dívida" in html
        assert "Custo de Vendas" in html
        assert "Forecast de Faturamento" in html
        assert "Fluxo de Caixa Projetado" in html

    def test_contains_date_filters(self, env: Environment):
        html = render("explorer.html", env)
        assert 'name="data_inicio"' in html
        assert 'name="data_fim"' in html

    def test_contains_status_filter(self, env: Environment):
        html = render("explorer.html", env)
        assert "Status" in html

    def test_contains_export_button(self, env: Environment):
        html = render("explorer.html", env)
        assert 'href="/api/export/xlsx"' in html

    def test_contains_pagination(self, env: Environment):
        html = render("explorer.html", env)
        assert "Anterior" in html or "Próxima" in html
        assert "Página" in html

    def test_contains_htmx_data_endpoint(self, env: Environment):
        html = render("explorer.html", env)
        assert 'hx-get="/api/data"' in html

    def test_table_id_present(self, env: Environment):
        html = render("explorer.html", env)
        assert 'id="explorer-tbody"' in html
        assert 'id="explorer-table-container"' in html

    def test_has_clear_button(self, env: Environment):
        html = render("explorer.html", env)
        assert "Limpar" in html


# ── CSS Tests ──────────────────────────────────────────────

class TestCustomCSS:
    """Tests for custom.css overrides."""

    def test_file_exists(self, project_root: Path):
        path = project_root / "app" / "static" / "css" / "custom.css"
        assert path.exists()

    def test_has_badge_classes(self, css_content: str):
        assert ".badge" in css_content
        assert ".badge-success" in css_content
        assert ".badge-danger" in css_content
        assert ".badge-warning" in css_content

    def test_has_htmx_request_class(self, css_content: str):
        assert ".htmx-request" in css_content

    def test_has_print_media_query(self, css_content: str):
        assert "@media print" in css_content

    def test_does_not_override_tailwind_unnecessarily(self, css_content: str):
        # Ensure we don't set hard-coded colors that break Tailwind utilities
        # Our overrides should be additive (badges, scrollbar, focus states)
        lines = css_content.splitlines()
        generic_rules = [l for l in lines if l.strip().startswith(".") or l.strip().startswith("{")]
        assert len(generic_rules) < 50  # reasonably small

    def test_has_form_focus_states(self, css_content: str):
        assert "focus" in css_content.lower()
        assert "box-shadow" in css_content.lower()


# ── JS Tests ───────────────────────────────────────────────

class TestChartsJS:
    """Tests for charts.js helpers."""

    def test_file_exists(self, project_root: Path):
        path = project_root / "app" / "static" / "js" / "charts.js"
        assert path.exists()

    def test_exports_renderLineChart(self, js_content: str):
        assert "function renderLineChart" in js_content
        assert "window.renderLineChart" in js_content

    def test_exports_renderDonutChart(self, js_content: str):
        assert "function renderDonutChart" in js_content
        assert "window.renderDonutChart" in js_content

    def test_exports_renderBarChart(self, js_content: str):
        assert "function renderBarChart" in js_content
        assert "window.renderBarChart" in js_content

    def test_has_common_options(self, js_content: str):
        assert "responsive" in js_content
        assert "maintainAspectRatio" in js_content

    def test_has_fpa_colors(self, js_content: str):
        assert "FPA_COLORS" in js_content

    def test_donut_has_cutout(self, js_content: str):
        assert "cutout" in js_content

    def test_has_tooltip_config(self, js_content: str):
        assert "tooltip" in js_content.lower()

    def test_has_legend_config(self, js_content: str):
        assert "legend" in js_content.lower()
