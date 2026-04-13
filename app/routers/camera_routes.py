import re
from pathlib import Path

from fastapi import APIRouter, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.config import settings

router = APIRouter(prefix="/api/cam", tags=["camera"])

IMAGES_DIR = settings.camera_images_dir
CAM_ID_RE = re.compile(r"^[a-z0-9_-]+$")


def normalize_cam_id(cam_id: str) -> str:
    safe_id = cam_id.strip().lower()
    if not safe_id or not CAM_ID_RE.fullmatch(safe_id):
        raise HTTPException(status_code=400, detail="cam_id inválido")
    if settings.allowed_camera_ids and safe_id not in settings.allowed_camera_ids:
        raise HTTPException(status_code=404, detail="Cámara no configurada")
    return safe_id


def require_camera_token(x_camera_token: str | None) -> None:
    if settings.camera_token and x_camera_token != settings.camera_token:
        raise HTTPException(status_code=401, detail="Token de cámara inválido")


def get_cam_dir(cam_id: str, create: bool) -> Path:
    safe_id = normalize_cam_id(cam_id)
    d = IMAGES_DIR / safe_id
    if create:
        d.mkdir(parents=True, exist_ok=True)
    return d


@router.post("/{cam_id}/frame")
async def upload_frame(
    cam_id: str,
    frame: UploadFile = File(...),
    x_camera_token: str | None = Header(default=None),
):
    """
    Recibe un frame JPEG de una ESP32-CAM y lo guarda como latest.jpg.
    """
    require_camera_token(x_camera_token)
    if frame.content_type not in ("image/jpeg", "image/jpg"):
        raise HTTPException(status_code=400, detail="Solo se aceptan imágenes JPEG")

    cam_dir = get_cam_dir(cam_id, create=True)
    latest_path = cam_dir / "latest.jpg"
    temp_path = cam_dir / ".latest.jpg.tmp"

    # Guardar el archivo en disco
    data = await frame.read()
    if not data:
        raise HTTPException(status_code=400, detail="El frame llegó vacío")
    if len(data) > settings.camera_max_bytes:
        raise HTTPException(status_code=413, detail="El frame excede el tamaño máximo permitido")
    if not data.startswith(b"\xff\xd8") or not data.endswith(b"\xff\xd9"):
        raise HTTPException(status_code=400, detail="El archivo no parece ser un JPEG válido")

    temp_path.write_bytes(data)
    temp_path.replace(latest_path)

    return {"ok": True, "cam": normalize_cam_id(cam_id), "bytes": len(data)}


@router.get("/{cam_id}/latest")
def get_latest(cam_id: str):
    """
    Devuelve la última imagen conocida de esa cámara.
    """
    cam_dir = get_cam_dir(cam_id, create=False)
    latest_path = cam_dir / "latest.jpg"

    if not latest_path.exists():
        raise HTTPException(status_code=404, detail="No hay imagen para esta cámara")

    return FileResponse(latest_path, media_type="image/jpeg")
