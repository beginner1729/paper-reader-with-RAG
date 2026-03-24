from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class CheckpointStore:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path_for_archive_url(self, archive_url: str) -> Path:
        digest = hashlib.sha256(archive_url.encode("utf-8")).hexdigest()[:24]
        return self.base_dir / f"{digest}.json"

    def load(self, archive_url: str) -> dict[str, Any] | None:
        file_path = self._path_for_archive_url(archive_url)
        if not file_path.exists():
            return None
        with file_path.open("r", encoding="utf-8") as file:
            data = json.load(file)
        if not isinstance(data, dict):
            return None
        if data.get("archive_url") != archive_url:
            return None
        return data

    def save(self, archive_url: str, state: dict[str, Any], completed_steps: list[str]) -> Path:
        file_path = self._path_for_archive_url(archive_url)
        payload = {
            "archive_url": archive_url,
            "completed_steps": completed_steps,
            "state": state,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        temp_path = file_path.with_suffix(".tmp")
        with temp_path.open("w", encoding="utf-8") as file:
            json.dump(payload, file, indent=2, ensure_ascii=True)
        temp_path.replace(file_path)
        return file_path

    def clear(self, archive_url: str) -> None:
        file_path = self._path_for_archive_url(archive_url)
        if file_path.exists():
            file_path.unlink()

    def clear_step(self, archive_url: str, step_id: str) -> bool:
        data = self.load(archive_url)
        if not data:
            return False

        raw_steps = data.get("completed_steps", [])
        completed_steps = [
            step for step in raw_steps if isinstance(step, str) and step != step_id
        ]
        state = data.get("state", {})
        if not isinstance(state, dict):
            state = {}

        self.save(
            archive_url=archive_url,
            state=state,
            completed_steps=completed_steps,
        )
        return True
