from pydantic import BaseModel
from .config import ROLE_EDITOR


class LoginRequest(BaseModel):
    username: str
    password: str


class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: str = ROLE_EDITOR


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
