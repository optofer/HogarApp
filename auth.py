from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

security = HTTPBasic()

usuarios_validos = {
    "Fernando": "1234",
    "Camila": "4567",
    "Marinela": "7890"
}

def verificar_credenciales(credentials: HTTPBasicCredentials = Depends(security)):
    username = credentials.username
    password = credentials.password

    if username not in usuarios_validos:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado",
            headers={"WWW-Authenticate": "Basic"},
        )

    contrasena_valida = secrets.compare_digest(usuarios_validos[username], password)
    if not contrasena_valida:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Contraseña incorrecta",
            headers={"WWW-Authenticate": "Basic"},
        )

    return username


