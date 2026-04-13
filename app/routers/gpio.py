import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.gpio_service import GPIOService

router = APIRouter(prefix="/api", tags=["gpio"])

_lock = asyncio.Lock()

class SetPin(BaseModel):
    on: bool

def make_router(gpio: GPIOService | None) -> APIRouter:
    r = APIRouter(prefix="/api", tags=["gpio"])

    def require_gpio() -> GPIOService:
        if gpio is None:
            raise HTTPException(status_code=503, detail="GPIO unavailable")
        return gpio

    @r.get("/gpio")
    async def list_gpio():
        service = require_gpio()
        return {"pins": [p.__dict__ for p in service.list_pins()]}

    @r.post("/gpio/{name}")
    async def set_gpio(name: str, payload: SetPin):
        service = require_gpio()
        if not service.has_pin(name):
            raise HTTPException(status_code=404, detail="Unknown pin")
        async with _lock:
            p = service.set_pin(name, payload.on)
            return p.__dict__

    @r.post("/gpio/{name}/toggle")
    async def toggle_gpio(name: str):
        service = require_gpio()
        if not service.has_pin(name):
            raise HTTPException(status_code=404, detail="Unknown pin")
        async with _lock:
            p = service.toggle_pin(name)
            return p.__dict__

    return r
