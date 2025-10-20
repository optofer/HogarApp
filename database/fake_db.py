# database/fake_db.py
import json
from pathlib import Path
from models.user import UserOut

DB_PATH = Path("database/usuarios.json")


def load_users():
    """Carga los usuarios desde el JSON, validando con UserOut."""
    if not DB_PATH.exists():
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        DB_PATH.write_text("[]", encoding="utf-8")
        return []

    try:
        data = json.loads(DB_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        data = []

    users = []
    for item in data:
        try:
            users.append(UserOut.model_validate(item))
        except Exception:
            # Si el JSON tiene un usuario incompleto, lo descarta
            continue
    return users


def save_users(users):
    """Guarda los usuarios en JSON usando model_dump()."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    data = []
    for u in users:
        try:
            data.append(u.model_dump())
        except AttributeError:
            # por compatibilidad con objetos tipo dict
            data.append(u)
    DB_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding="utf-8")


# Lista inicial de usuarios
Users_list = load_users()

