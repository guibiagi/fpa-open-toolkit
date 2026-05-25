"""Tests for :mod:`app.main` — FastAPI application."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Return a TestClient for the FP&A Open Toolkit app."""
    from app.main import app

    return TestClient(app)


class TestHealth:
    """Health and readiness endpoints."""

    def test_health_returns_ok(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.text == "OK"

    def test_docs_endpoint(self, client: TestClient) -> None:
        resp = client.get("/docs")
        assert resp.status_code == 200
        assert "swagger" in resp.text.lower() or "openapi" in resp.text.lower()

    def test_openapi_schema(self, client: TestClient) -> None:
        resp = client.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        assert schema["info"]["title"] == "FP&A Open Toolkit"
        assert "/health" in schema["paths"]


class TestPages:
    """Page routes should return 200 HTML."""

    PAGES = ["/", "/forecast", "/cashflow", "/working-capital", "/debt", "/explorer"]

    @pytest.mark.parametrize("path", PAGES)
    def test_page_returns_html(self, client: TestClient, path: str) -> None:
        resp = client.get(path)
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]


class TestAPI:
    """API endpoints return structured data (501 until engines are ready)."""

    def test_overview_returns_501(self, client: TestClient) -> None:
        resp = client.get("/api/overview")
        assert resp.status_code == 501
        assert "not implemented" in resp.json()["detail"].lower()

    def test_forecast_returns_200(self, client: TestClient) -> None:
        resp = client.get("/api/forecast")
        assert resp.status_code == 200
        data = resp.json()
        assert "historico" in data
        assert "forecast" in data
        assert len(data["forecast"]) == 12  # default horizon

    def test_cashflow_returns_200(self, client: TestClient) -> None:
        resp = client.get("/api/cashflow")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 30
        assert "saldo_final_dia" in data[0]

    def test_working_capital_returns_501(self, client: TestClient) -> None:
        resp = client.get("/api/working-capital")
        assert resp.status_code == 501

    def test_debt_returns_501(self, client: TestClient) -> None:
        resp = client.get("/api/debt")
        assert resp.status_code == 501


class TestErrorHandling:
    """Exception handlers."""

    def test_404_returns_json(self, client: TestClient) -> None:
        resp = client.get("/nonexistent")
        assert resp.status_code == 404
        data = resp.json()
        assert "detail" in data


class TestConfig:
    """Configuration is loaded correctly."""

    def test_settings_defaults(self) -> None:
        from app.config import settings

        assert settings.seed == 42
        assert settings.env == "development"
        assert settings.port == 8000

    def test_settings_is_development(self) -> None:
        from app.config import settings

        assert settings.is_development is True
        assert settings.is_production is False
