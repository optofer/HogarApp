from fastapi import APIRouter, Request, Query
from fastapi.responses import PlainTextResponse
import os
import numpy as np
from PIL import Image
from datetime import datetime

router = APIRouter()

@router.post("/upload_raw")
async def upload_raw(request: Request, cam: int = Query(...)):
    raw_data = await request.body()
    print(f"📥 Bytes recibidos de cam{cam}: {len(raw_data)}")

    # Guardar RAW temporal para depuración
    os.makedirs("database", exist_ok=True)
    raw_path = f"database/captura_cam{cam}.raw"
    prev_path = f"database/anterior_cam{cam}.raw"

    with open(raw_path, "wb") as f:
        f.write(raw_data)

    # Comparar con imagen anterior
    movimiento = False
    if os.path.exists(prev_path):
        raw1 = np.fromfile(prev_path, dtype=np.uint8)
        raw2 = np.frombuffer(raw_data, dtype=np.uint8)

        if len(raw1) == len(raw2):
            diferencia = np.abs(raw1.astype(int) - raw2.astype(int))
            cambio_total = np.sum(diferencia)
            print(f"🔍 Diferencia cam{cam}: {cambio_total}")
            if cambio_total > 100000:
                movimiento = True
    else:
        print(f"📷 Primera imagen cam{cam}, no hay comparación previa.")

    # Guardar como anterior para próxima comparación
    os.replace(raw_path, prev_path)

    # Convertir RAW a JPG
    width, height = 320, 240
    raw = np.frombuffer(raw_data, dtype=np.uint8)
    if len(raw) != width * height * 2:
        print(f"❌ RAW inválido cam{cam}: {len(raw)} bytes")
        return PlainTextResponse("❌ Imagen RAW con tamaño incorrecto")

    raw16 = raw.view(np.uint16).byteswap()  # <- Mejora calidad
    r = ((raw16 >> 11) & 0x1F) << 3
    g = ((raw16 >> 5) & 0x3F) << 2
    b = (raw16 & 0x1F) << 3
    rgb = np.stack((r, g, b), axis=-1).astype(np.uint8)

    try:
        img = Image.fromarray(rgb.reshape((height, width, 3)))
    except Exception as e:
        print("❌ Error al reconstruir imagen:", e)
        return PlainTextResponse("❌ Fallo al reconstruir imagen")


    # Carpeta de imágenes por cámara
    cam_dir = f"static/imagenes/cam{cam}"
    os.makedirs(cam_dir, exist_ok=True)

    # Guardar imagen actual
    jpg_path = os.path.join(cam_dir, f"cam{cam}.jpg")
    img.save(jpg_path, "JPEG")
    print(f"✅ Imagen cam{cam} guardada en {jpg_path}")

    # Guardar historial si hubo movimiento
    if movimiento:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        hist_name = os.path.join(cam_dir, f"cam{cam}_{timestamp}.jpg")
        img.save(hist_name, "JPEG")
        print(f"📁 Historial: {hist_name}")
