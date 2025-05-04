from fastapi.security import HTTPBasic, HTTPBasicCredentials
from auth import verificar_credenciales
from fastapi import Depends, HTTPException, status
import secrets
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import FastAPI
from routers import user_routes
from fastapi import WebSocket, WebSocketDisconnect
from routers import raw_routes

print("🚀 main.py se está ejecutando")

security = HTTPBasic()

# Definimos usuarios válidos una sola vez
usuarios_validos = {
    "Fernando": "1234",
    "Camila": "4567",
    "Marinela": "7890"
}

def verificar_credenciales(credentials: HTTPBasicCredentials = Depends(security)):
    username = credentials.username
    password = credentials.password

    if username not in usuarios_validos:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Basic"},
        )

    contrasena_valida = secrets.compare_digest(usuarios_validos[username], password)
    if not contrasena_valida:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña incorrecta",
            headers={"WWW-Authenticate": "Basic"},
        )

    return username

app = FastAPI()

# Incluir rutas de usuarios
app.include_router(user_routes.router)
app.include_router(raw_routes.router)
# Servir archivos estáticos (como HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Ruta raíz que entrega index.html
@app.get("/", response_class=FileResponse)
async def root(user: str = Depends(verificar_credenciales)):
	return FileResponse("static/index.html")



# Lista de conexiones activas
conexiones_websocket = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    conexiones_websocket.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            print(f"📩 Mensaje recibido: {data}")
            # reenviar a todos los clientes conectados (incluido quien lo envió)
            for conn in conexiones_websocket:
                await conn.send_text(data)

    except WebSocketDisconnect:
        conexiones_websocket.remove(websocket)
        print("❌ WebSocket desconectado")

from gpiozero import LED

gpio_map = {
    "GPIO0": LED(17),  # Pin 11 (Alarma)
    "GPIO2": LED(18),  # Pin 12 (Pánico)
    "GPIO4": LED(27),  # Pin 13 (Confort)
    "GPIO5": LED(22)   # Pin 15 (Riego)
}

