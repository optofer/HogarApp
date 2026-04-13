from __future__ import annotations
from dataclasses import dataclass
from typing import Dict
from gpiozero import OutputDevice

@dataclass(frozen=True)
class PinInfo:
    name: str
    bcm: int
    on: bool
    active_low: bool

class GPIOService:
    def __init__(self, pin_map: Dict[str, int], active_high: bool):
        self._pin_map = pin_map
        self._devices: Dict[str, OutputDevice] = {
            name: OutputDevice(bcm, active_high=active_high, initial_value=False)
            for name, bcm in pin_map.items()
        }
        self._active_low = (active_high is False)

    def has_pin(self, name: str) -> bool:
        return name in self._devices

    def list_pins(self) -> list[PinInfo]:
        return [
            PinInfo(name=name, bcm=self._pin_map[name], on=bool(dev.value), active_low=self._active_low)
            for name, dev in self._devices.items()
        ]

    def set_pin(self, name: str, on: bool) -> PinInfo:
        dev = self._devices[name]
        if on:
            dev.on()   # active_high=False => ON implica LOW físico (activa relé)
        else:
            dev.off()  # HIGH físico
        return PinInfo(name=name, bcm=self._pin_map[name], on=bool(dev.value), active_low=self._active_low)

    def toggle_pin(self, name: str) -> PinInfo:
        dev = self._devices[name]
        if dev.value:
            dev.off()
        else:
            dev.on()
        return PinInfo(name=name, bcm=self._pin_map[name], on=bool(dev.value), active_low=self._active_low)
