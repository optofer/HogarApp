# routers/user_routes.py
from fastapi import APIRouter, Depends, HTTPException
from models.user import UserCreate, UserOut
from database.fake_db import Users_list, save_users
from auth import verificar_credenciales  # si lo moviste a auth_basic.py, ajustá el import

router = APIRouter(tags=["users"])

# ---------- Helpers ----------
def _as_userout(obj) -> UserOut:
    # normaliza dicts o pydantic antiguos a UserOut
    if isinstance(obj, UserOut):
        return obj
    return UserOut.model_validate(obj)

def _next_id() -> int:
    try:
        return max((u.id for u in map(_as_userout, Users_list)), default=0) + 1
    except Exception:
        return 1

# ---------- GET: lista ----------
@router.get("/users", response_model=list[UserOut])
async def get_users(_: str = Depends(verificar_credenciales)):
    return [ _as_userout(u) for u in Users_list ]

# ---------- GET: por id ----------
@router.get("/user/{id}", response_model=UserOut)
async def get_user_by_id(id: int, _: str = Depends(verificar_credenciales)):
    for u in map(_as_userout, Users_list):
        if u.id == id:
            return u
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

# ---------- POST: crear ----------
@router.post("/user", response_model=UserOut)
async def create_user(user_data: UserCreate, _: str = Depends(verificar_credenciales)):
    new_id = _next_id()

    new_user = UserOut(
        id=new_id,
        username=user_data.username,
        email=user_data.email,
        name=None,
        surname=None,
        url=None,
    )

    Users_list.append(new_user)
    save_users(Users_list)   # asegúrate de que fake_db serializa con .model_dump()
    return new_user

# ---------- DELETE: borrar ----------
@router.delete("/user/{id}", response_model=UserOut)
async def delete_user(id: int, _: str = Depends(verificar_credenciales)):
    # buscar índice para remover
    for idx, u in enumerate(map(_as_userout, Users_list)):
        if u.id == id:
            removed = Users_list.pop(idx)
            save_users(Users_list)
            return _as_userout(removed)
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

# ---------- PUT: actualizar (reemplazo total) ----------
@router.put("/user/{id}", response_model=UserOut)
async def update_user(id: int, updated: UserOut, _: str = Depends(verificar_credenciales)):
    if id != updated.id:
        raise HTTPException(status_code=400, detail="El ID de la URL y del cuerpo deben coincidir")

    # reemplazo total
    for idx, u in enumerate(map(_as_userout, Users_list)):
        if u.id == id:
            Users_list[idx] = updated
            save_users(Users_list)
            return updated

    raise HTTPException(status_code=404, detail="Usuario no encontrado")

