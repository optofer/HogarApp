import os
from pathlib import Path

from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parents[1]


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_csv(name: str) -> set[str]:
    value = os.getenv(name, "")
    return {item.strip().lower() for item in value.split(",") if item.strip()}


class Settings(BaseModel):
    # GPIO en BCM
    pins: dict[str, int] = {
        "gpio16": 16,
        "gpio18": 18,
        "gpio24": 24,
        "gpio25": 25,
    }

    # Relés activos en LOW => active_high=False en gpiozero
    active_high: bool = False

    # Si es True, el proceso falla al arrancar cuando GPIO no está disponible.
    gpio_required: bool = _env_bool("GPIO_REQUIRED", False)

    # Almacenamiento y restricciones para frames remotos enviados por ESP32-CAM.
    camera_images_dir: Path = Path(os.getenv("CAMERA_IMAGES_DIR", str(BASE_DIR / "static" / "imagenes")))
    camera_max_bytes: int = int(os.getenv("CAMERA_MAX_BYTES", "2000000"))
    allowed_camera_ids: set[str] = _env_csv("ALLOWED_CAMERA_IDS")
    camera_token: str | None = os.getenv("CAMERA_TOKEN") or None


settings = Settings()
