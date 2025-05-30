from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import asyncio

clients = set()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except:
        clients.remove(websocket)

@router.post("/gpio_event")
async def gpio_event(request: Request):
    data = await request.json()
    pin = data["pin"]
    state = data["state"]
    msg = f"{pin}:{state}"
    # Enviar el evento a todos los clientes WebSocket conectados
    await asyncio.gather(*[client.send_text(msg) for client in clients])
    return JSONResponse({"ok": True})
