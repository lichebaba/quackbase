import uuid

from fastapi import APIRouter, Depends, HTTPException

from ..auth import get_auth_conn, close_user_db, require_permission, hash_password
from ..config import ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER, DB_BASE
from ..schemas import CreateUserRequest

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users")
async def list_users(user=Depends(require_permission("manage_users"))):
    conn = get_auth_conn()
    rows = conn.execute(
        "SELECT id, username, role, created_at FROM users ORDER BY created_at"
    ).fetchall()
    return {
        "users": [
            {"id": r[0], "username": r[1], "role": r[2], "created_at": str(r[3])}
            for r in rows
        ]
    }


@router.post("/users")
async def create_user(body: CreateUserRequest, user=Depends(require_permission("manage_users"))):
    if body.role not in (ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER):
        raise HTTPException(400, "无效角色，可选: admin / editor / viewer")
    new_id = str(uuid.uuid4())
    conn = get_auth_conn()
    try:
        conn.execute(
            "INSERT INTO users (id, username, password_hash, role) VALUES (?, ?, ?, ?)",
            [new_id, body.username, hash_password(body.password), body.role]
        )
        return {"success": True, "user": {"id": new_id, "username": body.username, "role": body.role}}
    except Exception:
        raise HTTPException(400, f"用户名 '{body.username}' 已存在")


@router.delete("/users/{user_id}")
async def delete_user(user_id: str, user=Depends(require_permission("manage_users"))):
    if user_id == user["sub"]:
        raise HTTPException(400, "不能删除自己")
    conn = get_auth_conn()
    conn.execute("DELETE FROM users WHERE id = ?", [user_id])
    close_user_db(user_id)
    db_file = DB_BASE / f"{user_id}.duckdb"
    if db_file.exists():
        db_file.unlink()
    wal_file = DB_BASE / f"{user_id}.duckdb.wal"
    if wal_file.exists():
        wal_file.unlink()
    return {"success": True}


@router.patch("/users/{user_id}/role")
async def update_role(user_id: str, body: dict, user=Depends(require_permission("manage_users"))):
    role = body.get("role")
    if role not in (ROLE_ADMIN, ROLE_EDITOR, ROLE_VIEWER):
        raise HTTPException(400, "无效角色")
    if user_id == user["sub"]:
        raise HTTPException(400, "不能修改自己的角色")
    conn = get_auth_conn()
    conn.execute("UPDATE users SET role = ? WHERE id = ?", [role, user_id])
    return {"success": True}
