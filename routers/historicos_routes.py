from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from database.historicos import obtener_eventos, registrar_evento

router = APIRouter()

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
HISTORICOS_PAGE = STATIC_DIR / "historicos.html"


@router.get("/api/historicos", response_class=JSONResponse)
async def api_historicos(limit: int = Query(100, ge=1, le=500), tipo: str | None = None):
    try:
        eventos = obtener_eventos(limit=limit, tipo=tipo)
        return {"ok": True, "eventos": eventos}
    except Exception as exc:
        return JSONResponse(status_code=500, content={"ok": False, "error": str(exc)})


@router.get("/historicos", response_class=HTMLResponse)
async def historicos_page():
    if HISTORICOS_PAGE.exists():
        return HTMLResponse(HISTORICOS_PAGE.read_text(encoding="utf-8"))
    return HTMLResponse("<h1>Históricos no disponibles</h1>")


# Evento de prueba al importar el módulo para validar que la base funciona.
registrar_evento(
    tipo="sistema",
    evento="Módulo de históricos iniciado",
    origen="historicos_routes",
    detalle="La base SQLite está lista para registrar eventos.",
)
