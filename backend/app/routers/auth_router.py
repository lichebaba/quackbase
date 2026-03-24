import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import (
    get_auth_conn, get_current_user, require_permission,
    hash_password, verify_password, create_token,
)
from ..config import ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER
from ..schemas import LoginRequest, ChangePasswordRequest

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
async def login(body: LoginRequest):
    conn = get_auth_conn()
    row = conn.execute(
        "SELECT id, username, password_hash, role FROM users WHERE username = ?",
        [body.username]
    ).fetchone()
    if not row or not verify_password(body.password, row[2]):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "用户名或密码错误")
    token = create_token(row[0], row[1], row[3])
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": row[0], "username": row[1], "role": row[3]},
    }


@router.get("/me")
async def me(user=Depends(get_current_user)):
    return {"id": user["sub"], "username": user["username"], "role": user["role"]}


@router.post("/change-password")
async def change_password(body: ChangePasswordRequest, user=Depends(get_current_user)):
    conn = get_auth_conn()
    row = conn.execute("SELECT password_hash FROM users WHERE id = ?", [user["sub"]]).fetchone()
    if not row or not verify_password(body.old_password, row[0]):
        raise HTTPException(400, "原密码错误")
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        [hash_password(body.new_password), user["sub"]]
    )
    return {"success": True}
