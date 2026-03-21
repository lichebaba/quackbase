from pathlib import Path
from typing import List

from ..config import UPLOAD_BASE
from . import StorageBackend


class LocalStorage(StorageBackend):
    """Local filesystem storage backend."""

    def _user_dir(self, user_id: str) -> Path:
        d = UPLOAD_BASE / user_id
        d.mkdir(parents=True, exist_ok=True)
        return d

    def save(self, user_id: str, filename: str, data: bytes) -> str:
        path = self._user_dir(user_id) / filename
        path.write_bytes(data)
        return str(path)

    def get_local_path(self, user_id: str, filename: str) -> Path:
        return self._user_dir(user_id) / filename

    def delete(self, user_id: str, filename: str) -> None:
        path = self._user_dir(user_id) / filename
        if path.exists():
            path.unlink()

    def list_files(self, user_id: str) -> List[str]:
        d = self._user_dir(user_id)
        return [f.name for f in d.iterdir() if f.is_file()]
