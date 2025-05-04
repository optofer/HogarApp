print("✅ raw_routes.py está siendo importado")

from fastapi import APIRouter, Request
from fastapi.responses import PlainTextResponse
import os
import numpy as np
from PIL import Image
from datetime import datetime

print("🧪 raw_routes.py fue cargado correctamente")

router = APIRouter()

@router.post("/upload_raw")
async def upload_raw(request: Request):
    raw_data = await request.body()
    print("📥 Bytes recibidos:", len(raw_data))

    # Archivos
    os.makedirs("database", exist_ok=True)
    raw_path = "database/captura.raw"
    prev_path = "database/anterior.raw"

    # Si ya había una captura anterior, la pasamos a anterior.raw
    if os.path.exists(raw_path):
        os.replace(raw_path, prev_path)
        print("📦 captura.raw movido a anterior.raw")

    # Guardar la nueva captura como captura.raw
    with open(raw_path, "wb") as f:
        f.write(raw_data)
    print("💾 captura.raw guardado")

    # Guardar en static/ultima.raw (para inspección)
    with open("static/ultima.raw", "wb") as f:
        f.write(raw_data)

    # Convertir a imagen JPG
    width, height = 320, 240
    raw = np.frombuffer(raw_data, dtype=np.uint8)

    if len(raw) != width * height * 2:
        print(f"❌ RAW inválido: {len(raw)} bytes")
        return PlainTextResponse("❌ Imagen RAW con tamaño incorrecto")

    raw16 = raw.view(np.uint16).byteswap()

    r = ((raw16 >> 11) & 0x1F) * 255 // 31
    g = ((raw16 >> 5) & 0x3F) * 255 // 63
    b = (raw16 & 0x1F) * 255 // 31

    rgb = np.stack((r, g, b), axis=-1).astype(np.uint8)


    print("🧪 RAW válido, reconstruyendo imagen...")
    print("👉 RAW shape antes de reshape:", rgb.shape)

    try:
        img = Image.fromarray(rgb.reshape((height,width, 3)))
        img.save("static/ultima.jpg", "JPEG")
        print("✅ ultima.jpg guardada")
    except Exception as e:
        print("❌ Error al reconstruir imagen:", e)
        return PlainTextResponse("❌ Fallo al reconstruir imagen")

    # Comparar con imagen anterior (si existe)
    movimiento = False
    if os.path.exists(prev_path):
        print("🔍 anterior.raw encontrado. Comparando...")
        raw1 = np.fromfile(prev_path, dtype=np.uint8)
        raw2 = np.frombuffer(raw_data, dtype=np.uint8)

        if len(raw1) == len(raw2):
            diferencia = np.abs(raw1.astype(int) - raw2.astype(int))
            cambio_total = np.sum(diferencia)
            print(f"📊 Diferencia total: {cambio_total}")

            if cambio_total > 1000:
                movimiento = True
        else:
            print("⚠️ Tamaño diferente. No se compara.")
    else:
        print("🆕 No hay anterior.raw, es la primera imagen.")

    # Guardar en historial si hay movimiento
    if movimiento:
        print("⚠️ Movimiento detectado. Guardando al historial...")
        hist_path = "static/imagenes"
        os.makedirs(hist_path, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        img_name = os.path.join(hist_path, f"{timestamp}.jpg")

        img.save(img_name, "JPEG")
        print(f"📁 Imagen guardada: {img_name}")
    else:
        print("✅ Sin movimiento significativo.")

    return {"status": "ok"}

