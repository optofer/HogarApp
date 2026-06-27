from typing import Set
from fastapi import WebSocket


class WSManager:
    def __init__(self):
        # Lista de conexiones activas (WebSockets)
        self.active: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        """Aceptar una nueva conexión WebSocket."""
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket):
        """Eliminar una conexión cerrada."""
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast_json(self, data):
        """Enviar un mensaje JSON a todos los clientes conectados."""
        dead = []
        for ws in list(self.active):
            try:
                await ws.send_json(data)
            except Exception:
                # Si falla, se desconecta y se elimina
                dead.append(ws)

        for ws in dead:
            self.disconnect(ws)

