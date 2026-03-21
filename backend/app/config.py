import os
import secrets
from pathlib import Path

# ===== CONFIG =====
SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-in-production-" + secrets.token_hex(16))
ALGORITHM = "HS256"
TOKEN_EXPIRE_HOURS = 24
UPLOAD_BASE = Path("./uploads")
DB_BASE = Path("./databases")
AUTH_DB = "./auth.duckdb"

UPLOAD_BASE.mkdir(exist_ok=True)
DB_BASE.mkdir(exist_ok=True)

# ===== ROLES =====
ROLE_ADMIN = "admin"
ROLE_EDITOR = "editor"
ROLE_VIEWER = "viewer"

ROLE_PERMISSIONS = {
    ROLE_ADMIN:  {"upload", "read", "delete", "manage_users"},
    ROLE_EDITOR: {"upload", "read", "delete"},
    ROLE_VIEWER: {"read"},
}
