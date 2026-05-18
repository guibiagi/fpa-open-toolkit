"""Tests for HTML templates — Issue #20.

Render each Jinja2 template with mock context and assert structural correctness.
No FastAPI app required — pure Jinja2 compilation + render.
"""

from __future__ import annotations

import datetime
from pathlib import Path

import pytest
from jinja2 import Environment, FileSystemLoader, select_autoescape


@pytest.fixture
def templates_dir() -> Path:
    return Path(__file__).parent.parent / "app" / "templates"


@pytest.fixture
def env(templates_dir: Path) -> Environment:
    return Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(["html", "xml"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )


class MockRequest:
    """Minimal mock for request.url.path in nav links."""
    class MockURL:
        def __init__(self, path: str):
            self.path = path
    def __init__(self, path: str = "/"):
        self.url = self.MockURL(path)


def render(template_name: str, env: Environment, **ctx) -> str:
    """Render a template with default mock context."""
    template = env.get_template(template_name)
    defaults = {"request": MockRequest()}
    defaults.update(ctx)
    return template.render(**defaults)


class TestBaseTemplate:
    """Tests for base.html — the layout foundation."""

    def test_renders_without_error(self, env: Environment):
        html = render("base.html", env)
        assert html  # non-empty

    def test_contains_html5_doctype(self, env: Environment):
        html = render("base.html", env)
        assert "<!DOCTYPE html>" in html

    def test_contains_tailwind_cdn(self, env: Environment):
        html = render("base.html", env)
        assert "cdn.tailwindcss.com" in html

    def test_contains_htmx_cdn(self, env: Environment):
        html = render("base.html", env)
        assert "unpkg.com/htmx.org" in html

    def test_contains_chartjs_cdn(self, env: Environment):
        html = render("base.html", env)
        assert "chart.js" in html.lower() or "chart.umd" in html

    def test_contains_custom_css_link(self, env: Environment):
        html = render("base.html", env)
        assert "custom.css" in html

    def test_contains_custom_js_link(self, env: Environment):
        html = render("base.html", env)
        assert "charts.js" in html

    def test_has_title_block(self, env: Environment, templates_dir: Path):
        src = (templates_dir / "base.html").read_text()
        assert "{% block title %}" in src

    def test_has_content_block(self, env: Environment, templates_dir: Path):
        src = (templates_dir / "base.html").read_text()
        assert "{% block content %}" in src

    def test_has_scripts_block(self, env: Environment, templates_dir: Path):
        src = (templates_dir / "base.html").read_text()
        assert "{% block scripts %}" in src

    def test_has_navbar(self, env: Environment):
        html = render("base.html", env)
        assert "<nav" in html
        assert "Dashboard" in html
        assert "Forecast" in html
        assert "Caixa" in html
        assert "Giro" in html
        assert "Dívida" in html
        assert "Explorer" in html

    def test_has_footer(self, env: Environment):
        html = render("base.html", env)
        assert "<footer" in html
        assert "GitHub" in html

    def test_navbar_highlights_active_page(self, env: Environment):
        html = render("base.html", env, request=MockRequest("/forecast"))
        # The active page should have accent/bg classes
        assert "bg-accent" in html or "bg-emerald" in html

    def test_mobile_menu_present(self, env: Environment):
        html = render("base.html", env)
        assert "mobile-menu" in html
        assert "hidden" in html  # starts hidden

    def test_meta_viewport(self, env: Environment):
        html = render("base.html", env)
        assert "width=device-width" in html


class TestIndexTemplate:
    """Tests for index.html (Overview / Dashboard)."""

    def test_extends_base(self, env: Environment):
        template = env.get_template("index.html")
        source = template.render(request=MockRequest("/"))
        assert "Dashboard" in source
        assert "FP&A Open Toolkit" in source

    def test_contains_cards_placeholder(self, env: Environment):
        html = render("index.html", env)
        assert "Receita 12m" in html
        assert "Variação YoY" in html
        assert "Saldo Caixa" in html
        assert "Menor Saldo" in html
        assert "Estoque" in html
        assert "Dívida" in html
        assert "NCG" in html

    def test_contains_chart_canvases(self, env: Environment):
        html = render("index.html", env)
        assert 'id="chart-revenue"' in html
        assert 'id="chart-forecast"' in html
        assert 'id="chart-cashflow"' in html
        assert 'id="chart-ncg"' in html

    def test_has_scripts_block_with_chartjs(self, env: Environment):
        html = render("index.html", env)
        assert "renderLineChart" in html
        assert "renderDonutChart" in html

    def test_contains_htmx_overview_endpoint(self, env: Environment):
        html = render("index.html", env)
        assert 'hx-get="/api/overview"' in html

    def test_links_to_detail_pages(self, env: Environment):
        html = render("index.html", env)
        assert 'href="/forecast"' in html
        assert 'href="/cashflow"' in html
        assert 'href="/working-capital"' in html


class TestForecastTemplate:
    """Tests for forecast.html (Revenue Forecast)."""

    def test_extends_base(self, env: Environment):
        html = render("forecast.html", env)
        assert "Forecast de Receita" in html

    def test_contains_scenario_buttons(self, env: Environment):
        html = render("forecast.html", env)
        assert "Base" in html
        assert "Otimista" in html
        assert "Pessimista" in html

    def test_contains_inputs(self, env: Environment):
        html = render("forecast.html", env)
        assert 'name="horizon"' in html
        assert 'name="otimista_pct"' in html
        assert 'name="pessimista_pct"' in html

    def test_contains_htmx_forecast_endpoint(self, env: Environment):
        html = render("forecast.html", env)
        assert 'hx-get="/api/forecast"' in html

    def test_contains_chart_canvas(self, env: Environment):
        html = render("forecast.html", env)
        assert 'id="chart-forecast-main"' in html

    def test_contains_stats_cards(self, env: Environment):
        html = render("forecast.html", env)
        assert "Média Proj. (Base)" in html
        assert "Máximo Proj." in html
        assert "Mínimo Proj." in html

    def test_contains_forecast_table(self, env: Environment):
        html = render("forecast.html", env)
        assert "Tabela de Forecast" in html
        assert 'id="forecast-table"' in html

    def test_contains_export_button(self, env: Environment):
        html = render("forecast.html", env)
        assert 'href="/api/export/xlsx"' in html
        assert "Exportar Excel" in html

    def test_scenario_buttons_have_data_attrs(self, env: Environment):
        html = render("forecast.html", env)
        assert 'data-scenario="base"' in html
        assert 'data-scenario="otimista"' in html
        assert 'data-scenario="pessimista"' in html
