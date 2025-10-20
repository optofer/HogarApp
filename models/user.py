# models/user.py  (Pydantic v2)
from pydantic import BaseModel, EmailStr, HttpUrl
from pydantic import ConfigDict

class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str  # solo al crear

class UserOut(UserBase):
    id: int
    name: str | None = None
    surname: str | None = None
    url: HttpUrl | None = None
    # Si devolvés objetos ORM o dicts con atributos:
    model_config = ConfigDict(from_attributes=True)

