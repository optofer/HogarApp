from fastapi import APIRouter, Request
from PIL import Image, ImageChops
import numpy as np
import os
from datetime import datetime

router = APIRouter()

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

# Procesar y guardar imagen para una cámara
def procesar_y_guardar_imagen(raw_data, cam_id):
    width, height = 320, 240
    raw = np.frombuffer(raw_data, dtype=np.uint8)
    raw16 = raw.view(np.uint16)

    r = ((raw16 >> 11) & 0x1F) << 3
    g = ((raw16 >> 5) & 0x3F) << 2
    b = (raw16 & 0x1F) << 3

    rgb = np.stack((r, g, b), axis=-1).astype(np.uint8)
    img = Image.fromarray(rgb.reshape((height, width, 3)))

    ultima_path = f"static/ultima_{cam_id}.jpg"
    hist_path = f"static/imagenes/{cam_id}"
    os.makedirs(hist_path, exist_ok=True)

    if hay_cambio_significativo(ultima_path, img):
        img.save(ultima_path, "JPEG")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        img.save(f"{hist_path}/{cam_id}_{timestamp}.jpg", "JPEG")

# Rutas para las 3 cámaras
@router.post("/cam1")
async def recibir_raw_cam1(request: Request):
    raw_data = await request.body()
    procesar_y_guardar_imagen(raw_data, "cam1")
    return {"status": "ok"}

@router.post("/cam2")
async def recibir_raw_cam2(request: Request):
    raw_data = await request.body()
    procesar_y_guardar_imagen(raw_data, "cam2")
    return {"status": "ok"}

@router.post("/cam3")
async def recibir_raw_cam3(request: Request):
    raw_data = await request.body()
    procesar_y_guardar_imagen(raw_data, "cam3")
    return {"status": "ok"}
