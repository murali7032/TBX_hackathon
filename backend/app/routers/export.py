import csv
import io
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from openpyxl import Workbook

from app.schemas import ExportRequest
from app.services.sessions import session_store

router = APIRouter(prefix="/export", tags=["export"])


def _csv_stream(columns: list[str], rows: list[list[Any]]) -> io.StringIO:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(columns)
    for row in rows:
        writer.writerow(row)
    buffer.seek(0)
    return buffer


def _xlsx_bytes(columns: list[str], rows: list[list[Any]]) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "evidence"
    ws.append(columns)
    for row in rows:
        ws.append(list(row))
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


@router.post("/csv")
def export_csv(body: ExportRequest) -> StreamingResponse:
    if not body.columns:
        raise HTTPException(status_code=400, detail="columns required")
    buffer = _csv_stream(body.columns, body.rows)
    filename = body.filename if body.filename.endswith(".csv") else f"{body.filename}.csv"
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/xlsx")
def export_xlsx(body: ExportRequest) -> StreamingResponse:
    if not body.columns:
        raise HTTPException(status_code=400, detail="columns required")
    data = _xlsx_bytes(body.columns, body.rows)
    filename = body.filename
    if not filename.endswith(".xlsx"):
        filename = f"{filename.rsplit('.', 1)[0]}.xlsx"
    return StreamingResponse(
        iter([data]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/csv/{session_id}")
def export_session_evidence(session_id: str) -> StreamingResponse:
    session = session_store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    evidence = session.last_evidence
    if not evidence or not evidence.get("columns"):
        raise HTTPException(status_code=404, detail="No evidence available for this session")
    buffer = _csv_stream(evidence["columns"], evidence.get("rows") or [])
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="evidence-{session_id[:8]}.csv"'
        },
    )


@router.get("/xlsx/{session_id}")
def export_session_xlsx(session_id: str) -> StreamingResponse:
    session = session_store.get(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    evidence = session.last_evidence
    if not evidence or not evidence.get("columns"):
        raise HTTPException(status_code=404, detail="No evidence available for this session")
    data = _xlsx_bytes(evidence["columns"], evidence.get("rows") or [])
    return StreamingResponse(
        iter([data]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="evidence-{session_id[:8]}.xlsx"'
        },
    )
