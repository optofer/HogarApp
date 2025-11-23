# raw_route.py
from fastapi import APIRouter, Request, Query
from PIL import Image, ImageChops, ImageDraw, ImageFont
import numpy as np
import os
import tempfile
import time
from datetime import datetime

router = APIRouter()

# Parámetros de imagen RAW (RGB565)
WIDTH, HEIGHT = 320, 240
BYTES_PER_PIXEL = 2
RAW_EXPECTED = WIDTH * HEIGHT * BYTES_PER_PIXEL

# Parámetros del overlay (timestamp)
TS_FONT_SIZE = 16
TS_PAD = 6
TS_BAR_HEIGHT = 28             # franja inferior que luego ignoramos en la comparación
FORZAR_GUARDADO_CADA_S = 1.5   # guarda al menos cada X s aunque no haya movimiento

# --- RUTA ÚNICA: /upload_raw?cam=1|2|3 ---
@router.post("/upload_raw")
async def upload_raw(request: Request, cam: int = Query(..., ge=1, le=99)):
    raw_data = await request.body()
    print(f"📥 Bytes recibidos de cam{cam}: {len(raw_data)}")

    # Validación de tamaño
    if len(raw_data) != RAW_EXPECTED:
        return {
            "status": "error",
            "detail": f"Tamaño RAW inválido: {len(raw_data)} (esperado {RAW_EXPECTED})."
        }

    cam_id = f"cam{cam}"
    procesar_y_guardar_imagen(raw_data, cam_id)
    return {"status": "ok"}

    # --- Procesado principal ---
def procesar_y_guardar_imagen(raw_data: bytes, cam_id: str) -> None:
    # Interpretar RGB565 (little-endian). Si tu flujo viene big-endian: usa dtype=">u2"
    raw16 = np.frombuffer(raw_data, dtype="<u2")

    # Extraer canales
    r = ((raw16 >> 11) & 0x1F).astype(np.uint8) << 3
    g = ((raw16 >> 5)  & 0x3F).astype(np.uint8) << 2
    b = ( raw16        & 0x1F).astype(np.uint8) << 3

    rgb = np.stack((r, g, b), axis=-1).reshape((HEIGHT, WIDTH, 3))
    img = Image.fromarray(rgb, mode="RGB")

    base_dir = "static/imagenes"
    ultima_path = f"{base_dir}/{cam_id}.jpg"
    hist_path = f"{base_dir}/{cam_id}"
    os.makedirs(hist_path, exist_ok=True)
    os.makedirs(base_dir, exist_ok=True)

    # 🔹 NUEVO: condiciones de inicialización/forzado


    no_historico = (len(os.listdir(hist_path)) == 0)
    muy_vieja = True

    try:
        # ¿cuánto hace que no se actualiza el JPG actual?
        muy_vieja = (time.time() - os.path.getmtime(ultima_path)) > 2.0
    except FileNotFoundError:
        # si no existe, lo tratamos como inicialización
        no_historico = True
        muy_vieja = True

    # 1) Detección de cambio en la escena (ignorando la franja del reloj)
    cambio = hay_cambio_significativo(
    ultima_path,
    img,
    ignore_bottom_px=TS_BAR_HEIGHT + 4  # <- si no tenés TS_BAR_HEIGHT, poné 28
)

    # 2) Forzar guardado por tiempo (para que el timestamp avance aunque esté quieto)
    forzar_tiempo = _paso_intervalo_minimo(ultima_path, FORZAR_GUARDADO_CADA_S)  # p.ej. 1.5


    # --- DECISIÓN FINAL ---
    if cambio or no_historico or muy_vieja or forzar_tiempo:
    # Agregar timestamp + cam_id antes de guardar
       img_annot = overlay_timestamp(img.copy(), cam_id)

    # Escritura atómica del "actual"
       tmp_fd, tmp_path = tempfile.mkstemp(prefix=f".{cam_id}_", suffix=".jpg", dir=base_dir)
    try:
        with os.fdopen(tmp_fd, "wb") as f:
            img_annot.save(f, "JPEG", quality=85, optimize=True, progressive=True)
        os.replace(tmp_path, ultima_path)
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass

    # Guardar histórico
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    hist_file = os.path.join(hist_path, f"{cam_id}_{timestamp}.jpg")
    img_annot.save(hist_file, "JPEG", quality=85, optimize=True, progressive=True)


    # --- Detección de cambios (ignora la franja inferior del reloj) ---
def hay_cambio_significativo(img1_path: str, img2: Image.Image, umbral_pix: int = 15,
                             fraccion: float = 0.05, ignore_bottom_px: int = 0) -> bool:
    """
    Compara la escena actual (img2) contra el último JPEG guardado.
    Ignora 'ignore_bottom_px' píxeles desde abajo (zona del timestamp) para no disparar falsos positivos.
    """
    try:
        with Image.open(img1_path) as img1:
            if img1.mode != "RGB":
                img1 = img1.convert("RGB")
            if img1.size != img2.size:
                img1 = img1.resize(img2.size)
    except FileNotFoundError:
        return True  # Primera imagen: guardar

    if img2.mode != "RGB":
        img2 = img2.convert("RGB")

    diff = ImageChops.difference(img1, img2).convert("L")
    np_diff = np.asarray(diff, dtype=np.uint8)

    # Ignorar franja inferior (donde dibujamos el reloj)
    if ignore_bottom_px > 0:
        h = np_diff.shape[0]
        start = max(0, h - ignore_bottom_px)
        np_diff[start:, :] = 0

    porcentaje = np.count_nonzero(np_diff > umbral_pix) / np_diff.size
    return porcentaje > fraccion

    # --- Utilidades de overlay y tiempo ---
def overlay_timestamp(img: Image.Image, cam_id: str) -> Image.Image:
    draw = ImageDraw.Draw(img)
    font = _load_font(16)
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # esquina inferior izquierda, con borde para contraste
    draw.text((8, img.height - 24), f"{cam_id}  {ts}", font=font,
              fill=(255,255,255), stroke_width=2, stroke_fill=(0,0,0))
    return img


def _load_font(size=16):
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ):
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            pass
    return ImageFont.load_default()


def _paso_intervalo_minimo(ultima_path: str, min_seconds: float) -> bool:
    try:
        mtime = os.path.getmtime(ultima_path)
        return (time.time() - mtime) >= min_seconds
    except OSError:
        return True  # no existe el archivo: guardar

