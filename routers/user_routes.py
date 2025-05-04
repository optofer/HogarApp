from fastapi import APIRouter
from database.fake_db import Users_list
from models.user import User
from auth import verificar_credenciales
from fastapi import Depends
from fastapi import HTTPException 
from database.fake_db import Users_list, save_users

router = APIRouter()

@router.get("/users", response_model=list[User])
async def get_users(user: str = Depends(verificar_credenciales)):
    return Users_list

@router.get("/user/{id}", response_model=User)
async def get_user_by_id(id: int, user: str = Depends(verificar_credenciales)):
    user_found = list(filter(lambda u: u.id == id, Users_list))
    if user_found:
        return user_found[0]
    return {"error": "Usuario no encontrado"}


@router.post("/user", response_model=User)
async def create_user(user_data: User, user: str = Depends(verificar_credenciales)):
    if any(u.id == user_data.id for u in Users_list):
        raise HTTPException(status_code=400, detail="El ID ya existe")

    Users_list.append(user_data)
    save_users(Users_list)
    return user_data



@router.delete("/user/{id}", response_model=User)
async def delete_user(id: int, user: str = Depends(verificar_credenciales)):
    user_to_delete = next((u for u in Users_list if u.id == id), None)

    if not user_to_delete:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    Users_list.remove(user_to_delete)
    save_users(Users_list)  # actualiza el archivo usuarios.json

    return user_to_delete

@router.put("/user/{id}", response_model=User)
async def update_user(id: int, updated_user: User, user: str = Depends(verificar_credenciales)):
    if id != updated_user.id:
        raise HTTPException(status_code=400, detail="El ID en la URL y en el cuerpo deben coincidir")

    for index, user in enumerate(Users_list):
        if user.id == id:
            Users_list[index] = updated_user
            save_users(Users_list)
            return updated_user

    raise HTTPException(status_code=404, detail="Usuario no encontrado")


