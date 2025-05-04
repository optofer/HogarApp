import json
from models.user import User

# Cargar usuarios desde archivo JSON
def load_users():
    with open("database/usuarios.json", "r") as f:
        data = json.load(f)
        return [User(**user) for user in data]

# Guardar usuarios en el archivo JSON
def save_users(users):
    with open("database/usuarios.json", "w") as f:
        json.dump([user.dict() for user in users], f, indent=4)

# Lista que se carga al iniciar
Users_list = load_users()

