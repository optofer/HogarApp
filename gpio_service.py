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

# Ajustar a tu cableado real
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
