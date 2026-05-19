"""Export router — downloadable reports.

Provides the consolidated Excel report endpoint that bundles all
financial data into a single multi-sheet ``.xlsx`` file.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO

router = APIRouter(prefix="/api/export", tags=["export"])

try:
    from export.xlsx_report import build_report
except ImportError:  # pragma: no cover
    build_report = None  # type: ignore[assignment]


@router.get("/xlsx")
def download_xlsx_report() -> StreamingResponse:
    """Download the full consolidated financial report as an Excel file.

    Returns a ``.xlsx`` with 6 sheets:
    1. Resumo Executivo
    2. Forecast de Receita
    3. Fluxo de Caixa Projetado
    4. Capital de Giro
    5. Endividamento
    6. Dados Brutos

    Returns ``501 Not Implemented`` if the report engine is not yet built.
    """
    if build_report is None:
        raise HTTPException(
            status_code=501,
            detail=(
                "Excel report engine not implemented yet. "
                "See src/export/xlsx_report.py (issue #8)."
            ),
        )

    buffer = BytesIO()
    build_report(buffer)
    buffer.seek(0)

    filename = "fpa_report.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
