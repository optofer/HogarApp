from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from gpio_service import set_gpio, get_all_states
import json

router = APIRouter()
clients = set()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    clients.add(websocket)
    print("[WS] Cliente conectado")

    # Enviar estado inicial
    await websocket.send_json({
        "type": "init",
        "states": get_all_states()
    })

    try:
        while True:
            data = await websocket.receive_text()
            print("[WS] Recibido:", data)

            try:
                msg = json.loads(data)
            except:
                print("[WS] ERROR: JSON inválido")
                continue

            # --- FORMATO NUEVO ---
            if msg.get("type") == "set":
                pin = msg.get("pin")
                state = msg.get("state")

            # --- FORMATO VIEJO ---
            else:
                pin = msg.get("gpio")
                state = msg.get("state")

            if pin is None or state is None:
                print("[WS] ERROR: mensaje sin pin/state")
                continue

            print(f"[GPIO] Cambiando {pin} -> {state}")
            set_gpio(pin, state)

            # Preparar broadcast con estados reales
            await broadcast({
                "type": "update",
                "states": get_all_states()
            })

    except WebSocketDisconnect:
        print("[WS] Cliente desconectado")
        clients.discard(websocket)


async def broadcast(message: dict):
    dead = []
    for ws in list(clients):
        try:
            await ws.send_json(message)
        except:
            dead.append(ws)

    for ws in dead:
        clients.discard(ws)

