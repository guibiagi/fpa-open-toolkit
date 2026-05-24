"""Application configuration via pydantic-settings.

Reads from environment variables with sensible defaults.
Copy ``.env.example`` to ``.env`` to override locally.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """FP&A Open Toolkit application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Random seed ───────────────────────────────────────────────────────
    seed: int = 42

    # ── Paths ─────────────────────────────────────────────────────────────
    data_dir: str = "data/synthetic"
    output_dir: str = "data/outputs"
    templates_dir: str = "app/templates"
    static_dir: str = "app/static"

    # ── Environment ───────────────────────────────────────────────────────
    env: str = "development"

    # ── Server ────────────────────────────────────────────────────────────
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False

    @property
    def is_production(self) -> bool:
        return self.env == "production"

    @property
    def is_development(self) -> bool:
        return self.env in ("development", "dev")


# Singleton
settings = Settings()

# Ensure output directory exists on import
Path(settings.output_dir).mkdir(parents=True, exist_ok=True)
