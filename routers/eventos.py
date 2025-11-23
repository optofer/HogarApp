from fastapi import APIRouter, Request, WebSocket
from fastapi.responses import JSONResponse
import asyncio

router = APIRouter() 
clients = set()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except Exception:
        if websocket in clients:
            clients.remove(websocket)

@router.post("/gpio_event")
async def gpio_event(request: Request):
    data = await request.json()
    pin = data["pin"]
    state = data["state"]
    msg = f"{pin}:{state}"
    # Enviar evento a todos los websockets conectados
    await asyncio.gather(*[client.send_text(msg) for client in clients])
    return JSONResponse({"ok": True})

