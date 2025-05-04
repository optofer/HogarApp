from fastapi import APIRouter, Request, Query
from fastapi.responses import PlainTextResponse
from PIL import Image, ImageChops
import numpy as np
import os
from datetime import datetime

router = APIRouter()

# Ruta genérica para recibir datos RAW y determinar a qué cámara per>
@router.post("/upload_raw")
async def upload_raw(request: Request, cam: int = Query(...)):
    raw_data = await request.body()
    print(f"📥 Bytes recibidos de cam{cam}: {len(raw_data)}")
    cam_id = f"cam{cam}"
    procesar_y_guardar_imagen(raw_data, cam_id)
    return {"status": "ok"}

# Procesar y guardar imagen para una cámara
def procesar_y_guardar_imagen(raw_data, cam_id):
    width, height = 320, 240
    raw = np.frombuffer(raw_data, dtype=np.uint8)

    raw16 = raw.view(np.uint16).byteswap()  # <- Mejora calidad
    r = ((raw16 >> 11) & 0x1F) << 3
    g = ((raw16 >> 5) & 0x3F) << 2
    b = (raw16 & 0x1F) << 3
    rgb = np.stack((r, g, b), axis=-1).astype(np.uint8)

    rgb = np.stack((r, g, b), axis=-1).astype(np.uint8)
    img = Image.fromarray(rgb.reshape((height, width, 3)))

    ultima_path = f"static/imagenes/{cam_id}.jpg"  # Aquí guarda la imagen actual
    hist_path = f"static/imagenes/{cam_id}"        # Carpeta de historial
    os.makedirs(hist_path, exist_ok=True)

    if hay_cambio_significativo(ultima_path, img):
        img.save(ultima_path, "JPEG")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        img.save(f"{hist_path}/{cam_id}_{timestamp}.jpg", "JPEG")

# Función común para detección de cambios
def hay_cambio_significativo(img1_path, img2):
    try:
        img1 = Image.open(img1_path).resize(img2.size)
    except FileNotFoundError:
        return True  # Si no existe imagen previa, se guarda

    diff = ImageChops.difference(img1, img2).convert("L")
    np_diff = np.array(diff)
    porcentaje = np.count_nonzero(np_diff > 30) / np_diff.size
    return porcentaje > 0.05


