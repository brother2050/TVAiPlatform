import os
import shutil
import json
from pathlib import Path
from typing import List, Optional


class LocalStorage:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve(self, relative_path: str) -> Path:
        return self.base_path / relative_path

    def save_text(self, relative_path: str, content: str) -> str:
        full_path = self._resolve(relative_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding="utf-8")
        return str(full_path)

    def save_bytes(self, relative_path: str, data: bytes) -> str:
        full_path = self._resolve(relative_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_bytes(data)
        return str(full_path)

    def save_file(self, relative_path: str, source_path: str) -> str:
        full_path = self._resolve(relative_path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, full_path)
        return str(full_path)

    def read_text(self, relative_path: str) -> str:
        return self._resolve(relative_path).read_text(encoding="utf-8")

    def read_bytes(self, relative_path: str) -> bytes:
        return self._resolve(relative_path).read_bytes()

    def exists(self, relative_path: str) -> bool:
        return self._resolve(relative_path).exists()

    def delete(self, relative_path: str):
        full_path = self._resolve(relative_path)
        if full_path.is_dir():
            shutil.rmtree(full_path)
        elif full_path.exists():
            full_path.unlink()

    def delete_project(self, project_id: str):
        self.delete(f"projects/{project_id}")

    def list_dir(self, relative_path: str) -> List[str]:
        full_path = self._resolve(relative_path)
        if not full_path.exists():
            return []
        return [str(p.relative_to(self.base_path)) for p in full_path.iterdir()]

    def get_project_path(self, project_id: str) -> Path:
        return self._resolve(f"projects/{project_id}")

    def get_segment_path(self, project_id: str, segment_id: str) -> Path:
        return self._resolve(f"projects/{project_id}/segments/{segment_id}")

    def get_shot_path(self, project_id: str, segment_id: str, shot_id: str) -> Path:
        return self._resolve(f"projects/{project_id}/segments/{segment_id}/shots/{shot_id}")


_storage_instance: Optional[LocalStorage] = None


def get_storage() -> LocalStorage:
    global _storage_instance
    if _storage_instance is None:
        from shared.config import get_config
        cfg = get_config()
        storage_path = cfg["storage"]["local_path"]
        _storage_instance = LocalStorage(storage_path)
    return _storage_instance