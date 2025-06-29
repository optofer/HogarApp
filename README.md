# ESP32-CAM + FastAPI Server

Proyecto de vigilancia con ESP32-CAM enviando imágenes RAW a un servidor FastAPI alojado en Raspberry Pi.

## Funcionalidades

- Conversión de imágenes RAW RGB565 a JPG
- Detección de movimiento
- Historial de imágenes
- Visualización en navegador
- Control GPIO vía WebSocket

## Requisitos

- Raspberry Pi con Python 3.11
- ESP32-CAM
- FastAPI + Uvicorn

## Cómo correrlo

```bash
uvicorn main:app --reload --host 0.0.0.0
# raspberry_fastapiserver
