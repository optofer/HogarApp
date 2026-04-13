from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.config import settings
from app.services.gpio_service import GPIOService
from app.routers.gpio import make_router
from app.routers.camera_routes import router as camera_router


def create_app() -> FastAPI:
    # Una sola instancia de FastAPI
    app = FastAPI(title="fastapi_server2")
    settings.camera_images_dir.mkdir(parents=True, exist_ok=True)

    # Servicio GPIO
    gpio = None
    gpio_error = None
    try:
        gpio = GPIOService(settings.pins, active_high=settings.active_high)
    except Exception as exc:
        gpio_error = str(exc)
        if settings.gpio_required:
            raise

    # Opcional: guardar en state por si lo usás en otros lados
    app.state.gpio = gpio
    app.state.gpio_error = gpio_error

    # Rutas GPIO (las que ya tenías)
    app.include_router(make_router(gpio))

    # Rutas de cámara (nuevo)
    app.include_router(camera_router)

    # Healthcheck simple
    @app.get("/health")
    async def health():
        return {
            "ok": gpio is not None or not settings.gpio_required,
            "gpio": {
                "available": gpio is not None,
                "required": settings.gpio_required,
                "error": gpio_error,
            },
            "camera": {
                "images_dir": str(settings.camera_images_dir),
                "max_bytes": settings.camera_max_bytes,
                "allowed_ids": sorted(settings.allowed_camera_ids),
                "token_required": bool(settings.camera_token),
            },
        }

    @app.get("/cams", response_class=HTMLResponse)
    async def cams_view():
        return """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Monitoreo de Camaras</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f3efe7;
      --panel: #fffaf2;
      --ink: #1e1e1e;
      --muted: #6e6558;
      --line: #d8cfbf;
      --accent: #b5522d;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, #fff7e8 0, transparent 28%),
        linear-gradient(135deg, #efe8dc 0%, var(--bg) 100%);
      min-height: 100vh;
    }
    .wrap {
      max-width: 1200px;
      margin: 0 auto;
      padding: 24px;
    }
    h1 {
      margin: 0 0 8px;
      font-size: 2rem;
    }
    p {
      margin: 0 0 24px;
      color: var(--muted);
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 20px;
    }
    .card {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      overflow: hidden;
      box-shadow: 0 18px 40px rgba(54, 38, 24, 0.08);
    }
    .card header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 14px 16px;
      border-bottom: 1px solid var(--line);
    }
    .badge {
      padding: 4px 10px;
      border-radius: 999px;
      background: rgba(181, 82, 45, 0.12);
      color: var(--accent);
      font-size: 0.85rem;
    }
    img {
      display: block;
      width: 100%;
      aspect-ratio: 4 / 3;
      object-fit: cover;
      background: #ddd6ca;
    }
    .meta {
      padding: 12px 16px 16px;
      font-size: 0.95rem;
      color: var(--muted);
    }
    .toolbar {
      display: flex;
      gap: 12px;
      align-items: center;
      flex-wrap: wrap;
      margin-bottom: 18px;
    }
    button {
      border: 0;
      border-radius: 999px;
      background: var(--accent);
      color: white;
      padding: 10px 14px;
      font: inherit;
      cursor: pointer;
    }
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Monitoreo de Camaras</h1>
    <p>Vista rapida de cam1 y cam2 con refresco automatico cada 3 segundos.</p>
    <div class="toolbar">
      <button type="button" onclick="refreshFrames()">Actualizar ahora</button>
      <span id="status">Esperando primer refresco...</span>
    </div>
    <div class="grid">
      <section class="card">
        <header>
          <strong>cam1</strong>
          <span class="badge">ESP32-CAM</span>
        </header>
        <img id="cam1" alt="cam1" src="/api/cam/cam1/latest">
        <div class="meta">Endpoint: /api/cam/cam1/latest</div>
      </section>
      <section class="card">
        <header>
          <strong>cam2</strong>
          <span class="badge">ESP32-CAM</span>
        </header>
        <img id="cam2" alt="cam2" src="/api/cam/cam2/latest">
        <div class="meta">Endpoint: /api/cam/cam2/latest</div>
      </section>
    </div>
  </div>
  <script>
    const cameraIds = ["cam1", "cam2"];
    const status = document.getElementById("status");

    function refreshFrames() {
      const ts = Date.now();
      for (const cameraId of cameraIds) {
        document.getElementById(cameraId).src = `/api/cam/${cameraId}/latest?t=${ts}`;
      }
      status.textContent = `Ultima actualizacion: ${new Date().toLocaleTimeString()}`;
    }

    refreshFrames();
    setInterval(refreshFrames, 3000);
  </script>
</body>
</html>
        """

    return app


app = create_app()
