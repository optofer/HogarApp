import pigpio



# Instancia del daemon pigpio
pi = pigpio.pi()
if not pi.connected:
    raise RuntimeError("No se pudo conectar a pigpiod. Ejecutá: sudo systemctl start pigpiod")

# Mapa BCM real
PIN_MAP = {
    "GPIO0": 17,
    "GPIO2": 27,
    "GPIO4": 22,
    "GPIO5": 23
}

# Estados en memoria
GPIO_STATE = {name: 0 for name in PIN_MAP}

# Inicializar pines como salida
for name, bcm in PIN_MAP.items():
    pi.set_mode(bcm, pigpio.OUTPUT)
    pi.write(bcm, 0)

def set_gpio(name: str, state: int) -> bool:
    if name not in PIN_MAP:
        return False
    bcm = PIN_MAP[name]
    pi.write(bcm, 1 if state else 0)
    GPIO_STATE[name] = state
    return True

def get_all_states():
    return GPIO_STATE.copy()

