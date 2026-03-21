from abc import ABC, abstractmethod
from pathlib import Path
from typing import List


class StorageBackend(ABC):
    """Abstract base class for file storage backends."""

    @abstractmethod
    def save(self, user_id: str, filename: str, data: bytes) -> str:
        ...

    @abstractmethod
    def get_local_path(self, user_id: str, filename: str) -> Path:
        ...

    @abstractmethod
    def delete(self, user_id: str, filename: str) -> None:
        ...

    @abstractmethod
    def list_files(self, user_id: str) -> List[str]:
        ...


def get_storage() -> StorageBackend:
    from .local import LocalStorage
    return LocalStorage()
