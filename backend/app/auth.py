import hashlib
import uuid
from datetime import datetime, timedelta

import duckdb
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import SECRET_KEY, ALGORITHM, TOKEN_EXPIRE_HOURS, AUTH_DB, DB_BASE, ROLE_PERMISSIONS, ROLE_ADMIN

bearer_scheme = HTTPBearer()


# ===== AUTH DB =====
def get_auth_conn():
    conn = duckdb.connect(AUTH_DB)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id VARCHAR PRIMARY KEY,
            username VARCHAR UNIQUE NOT NULL,
            password_hash VARCHAR NOT NULL,
            role VARCHAR NOT NULL DEFAULT 'editor',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    return conn


def init_admin():
    conn = get_auth_conn()
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count == 0:
        admin_id = str(uuid.uuid4())
        conn.execute(
            "INSERT INTO users (id, username, password_hash, role) VALUES (?, ?, ?, ?)",
            [admin_id, "admin", hash_password("admin123"), ROLE_ADMIN]
        )
        print("Default admin created  ->  admin / admin123  (please change!)")
    conn.close()


# ===== PER-USER DB =====
def get_user_db(user_id: str):
    return duckdb.connect(str(DB_BASE / f"{user_id}.duckdb"))


# ===== PASSWORD =====
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(plain: str, hashed: str) -> bool:
    return hash_password(plain) == hashed


# ===== JWT =====
def create_token(user_id: str, username: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    return jwt.encode(
        {"sub": user_id, "username": username, "role": role, "exp": expire},
        SECRET_KEY, algorithm=ALGORITHM
    )


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token 已过期，请重新登录")
    except jwt.InvalidTokenError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token 无效")


# ===== AUTH DEPENDENCY =====
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    return decode_token(credentials.credentials)


def require_permission(permission: str):
    def checker(user=Depends(get_current_user)):
        role = user.get("role", "viewer")
        if permission not in ROLE_PERMISSIONS.get(role, set()):
            raise HTTPException(status.HTTP_403_FORBIDDEN, f"权限不足（需要 {permission}）")
        return user
    return checker
