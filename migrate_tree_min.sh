#!/usr/bin/env bash
set -euo pipefail

ROOT="$(pwd)"
echo ">> Trabajando en: $ROOT"

# Carpetas necesarias
mkdir -p static/imagenes/cam1 static/imagenes/cam2 static/imagenes/cam3
mkdir -p static/images
mkdir -p database deploy
touch routers/__init__.py

# Mover HTML viejos a backup (dejando index.html actual en static/)
mkdir -p static/_old_html
for f in index_old.html index_old1.html termica.html vigil.html warnin.html; do
  if [ -f "static/$f" ]; then
    mv "static/$f" "static/_old_html/$f"
    echo ">> movido static/$f -> static/_old_html/$f"
  elif [ -f "$f" ]; then
    mv "$f" "static/_old_html/$f"
    echo ">> movido $f -> static/_old_html/$f"
  fi
done

# Verificación de Spectral
if [ -d "static/assets" ]; then
  echo ">> OK: Spectral assets en static/assets"
else
  echo "!! No encuentro static/assets (CSS/JS de Spectral). Revisar."
fi

# gpio_service.py (si falta)
if [ ! -f "gpio_service.py" ]; then
cat > gpio_service.py <<'PY'
import os

IS_PI = os.uname().machine.startswith("arm") or os.uname().machine.startswith("aarch64")

class GPIOBase:
    def setup(self, pin: int): raise NotImplementedError
    def write(self, pin: int, state: int) -> bool: raise NotImplementedError
    def read(self, pin: int) -> int: raise NotImplementedError

class MockGPIO(GPIOBase):
    def __init__(self): self.state = {}
    def setup(self, pin: int): self.state.setdefault(pin, 0)
    def write(self, pin: int, state: int) -> bool:
        self.state[pin] = 1 if state else 0; return True
    def read(self, pin: int) -> int: return self.state.get(pin, 0)

class RPiGPIO(GPIOBase):
    def __init__(self):
        import RPi.GPIO as GPIO
        self.GPIO = GPIO
        self.GPIO.setmode(GPIO.BCM)
        self.GPIO.setwarnings(False)
    def setup(self, pin: int): self.GPIO.setup(pin, self.GPIO.OUT, initial=self.GPIO.LOW)
    def write(self, pin: int, state: int) -> bool:
        self.GPIO.output(pin, self.GPIO.HIGH if state else self.GPIO.LOW); return True
    def read(self, pin: int) -> int: return 1 if self.GPIO.input(pin) == self.GPIO.HIGH else 0

PIN_MAP = {"GPIO0": 17, "GPIO2": 27, "GPIO4": 22, "GPIO5": 23}

if IS_PI:
    try:
        gpio = RPiGPIO()
    except Exception as e:
        print(f"[GPIO] Fallo RPi.GPIO, uso Mock: {e}")
        gpio = MockGPIO()
else:
    gpio = MockGPIO()

for name, bcm in PIN_MAP.items(): gpio.setup(bcm)
GPIO_STATE = {name: 0 for name in PIN_MAP}

def set_gpio(name: str, state: int) -> bool:
    if name not in PIN_MAP: return False
    bcm = PIN_MAP[name]
    ok = gpio.write(bcm, 1 if state else 0)
    if ok: GPIO_STATE[name] = 1 if state else 0
    return ok

def get_all_states(): return GPIO_STATE.copy()
PY
  echo ">> creado gpio_service.py"
fi

# ws_manager.py (si falta)
if [ ! -f "ws_manager.py" ]; then
cat > ws_manager.py <<'PY'
from typing import Set
from fastapi import WebSocket

class WSManager:
    def __init__(self): self.active: Set[WebSocket] = set()
    async def connect(self, ws: WebSocket): await ws.accept(); self.active.add(ws)
    def disconnect(self, ws: WebSocket): self.active.discard(ws)
    async def broadcast_json(self, data):
        dead = []
        for ws in list(self.active):
            try: await ws.send_json(data)
            except Exception: dead.append(ws)
        for d in dead: self.disconnect(d)
PY
  echo ">> creado ws_manager.py"
fi

echo ">> Migración mínima completada."
echo "   - Conservamos static/index.html y static/assets (Spectral)."
echo "   - Aseguradas carpetas de cámaras en static/imagenes/..."
echo "   - HTML viejos a static/_old_html/ (si estaban en static/ o raíz)."
