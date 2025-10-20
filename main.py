# main.py
from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

import secrets
import os
from PIL import Image
from gpiozero import LED

# Routers
from routers import user_routes, raw_routes
# Si tenés más routers:
# from routers import eventos, nuevo_raw_route, viejo_raw_routes

print("🚀 main.py se está ejecutando")

# ---------- AUTENTICACIÓN BASIC ----------
security = HTTPBasic()

USUARIOS_VALIDOS = {
    "Fernando": "1234",
    "Camila":   "4567",
    "Marinela": "7890",
}

def verificar_credenciales(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    username = credentials.username
    password = credentials.password

    if username not in USUARIOS_VALIDOS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Basic"},
        )

    if not secrets.compare_digest(USUARIOS_VALIDOS[username], password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña incorrecta",
            headers={"WWW-Authenticate": "Basic"},
        )
    return username

# ---------- APP ----------
app = FastAPI(
    title="fastapi_server",
    version="1.0.0",
    docs_url=None,       # desactivo docs por defecto
    redoc_url=None,      # desactivo redoc por defecto
    openapi_url=None,    # desactivo openapi por defecto
    # Protege TODAS las rutas HTTP con Basic
    dependencies=[Depends(verificar_credenciales)]
)

# ---------- ARCHIVOS ESTÁTICOS ----------
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------- INDEX ----------
@app.get("/", response_class=FileResponse)
async def root():
    return FileResponse("static/index.html")

# ---------- CREACIÓN DE IMÁGENES NEGRAS SI NO EXISTEN ----------
carpetas = {
    "cam1": "static/imagenes/cam1.jpg",
    "cam2": "static/imagenes/cam2.jpg",
    "cam3": "static/imagenes/cam3.jpg",
}
for _, path in carpetas.items():
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        Image.new("RGB", (320, 240), (0, 0, 0)).save(path, "JPEG")

# ---------- ROUTERS (quedan protegidos por la dependencia global) ----------
app.include_router(user_routes.router)
app.include_router(raw_routes.router)
# app.include_router(eventos.router)
# app.include_router(nuevo_raw_route.router)
# app.include_router(viejo_raw_routes.router)

# ---------- DOCS PROTEGIDOS ----------
@app.get("/openapi.json", response_class=JSONResponse)
def openapi_json(_: str = Depends(verificar_credenciales)):
    return get_openapi(title=app.title, version=app.version, routes=app.routes)

@app.get("/docs", response_class=HTMLResponse)
def docs(_: str = Depends(verificar_credenciales)):
    return get_swagger_ui_html(openapi_url="/openapi.json", title=f"{app.title} - Docs")

@app.get("/redoc", response_class=HTMLResponse)
def redoc(_: str = Depends(verificar_credenciales)):
    return get_redoc_html(openapi_url="/openapi.json", title=f"{app.title} - ReDoc")

# ---------- GPIO ----------
gpio_map = {
    "GPIO0": LED(17),  # Pin 11 (Alarma)
    "GPIO2": LED(18),  # Pin 12 (Pánico)
    "GPIO4": LED(27),  # Pin 13 (Confort)
    "GPIO5": LED(22),  # Pin 15 (Riego)
}

# ---------- WEBSOCKET (nota: no usa Basic del navegador) ----------
conexiones_websocket = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    conexiones_websocket.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            print(f"📩 Mensaje recibido: {data}")

            # Broadcast
            for conn in conexiones_websocket:
                await conn.send_text(data)

            # Procesar comando GPIO: "GPIO4:1"
            try:
                gpio, estado = data.split(":")
                if gpio in gpio_map:
                    if estado == "1":
                        gpio_map[gpio].off()  # LOW enciende LED (Freenove)
                    else:
                        gpio_map[gpio].on()   # HIGH apaga LED
                    print(f"⚙️ {gpio} cambiado a {'ON' if estado == '1' else 'OFF'}")
                else:
                    print(f"⚠️ GPIO no reconocido: {gpio}")
            except Exception as e:
                print(f"⚠️ Error procesando GPIO: {e}")

    except WebSocketDisconnect:
        if websocket in conexiones_websocket:
            conexiones_websocket.remove(websocket)
        print("❌ WebSocket desconectado")

