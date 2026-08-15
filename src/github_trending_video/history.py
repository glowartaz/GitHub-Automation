from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path

from .models import RepoMetadata


@dataclass(slots=True)
class HistoryEntry:
    node_id: str
    source_node_id: str
    full_name: str
    source_full_name: str
    featured_at: str
    run_id: str
    rank: int


class FeaturedHistory:
    def __init__(self, path: Path):
        self.path = path
        self.data = self._load()

    def _load(self) -> dict:
        if not self.path.exists():
            return {"schema_version": 1, "repositories": []}
        data = json.loads(self.path.read_text(encoding="utf-8"))
        if data.get("schema_version") != 1 or not isinstance(data.get("repositories"), list):
            raise ValueError(f"Invalid featured history: {self.path}")
        return data

    @property
    def used_ids(self) -> set[str]:
        ids: set[str] = set()
        for item in self.data["repositories"]:
            ids.update(x for x in (item.get("node_id"), item.get("source_node_id")) if x)
        return ids

    @property
    def used_names(self) -> set[str]:
        names: set[str] = set()
        for item in self.data["repositories"]:
            for key in ("full_name", "source_full_name"):
                if item.get(key):
                    names.add(item[key].lower())
        return names

    def contains(self, repo: RepoMetadata) -> bool:
        return bool(repo.identity_ids & self.used_ids) or any(
            name.lower() in self.used_names
            for name in (repo.full_name, repo.source_full_name)
            if name
        )

    def record(self, repos: list[RepoMetadata], run_id: str) -> None:
        current_ids = self.used_ids
        for rank, repo in enumerate(repos, start=1):
            if repo.identity_ids & current_ids:
                raise ValueError(f"Duplicate repository blocked: {repo.full_name}")
            entry = HistoryEntry(
                node_id=repo.node_id,
                source_node_id=repo.source_node_id,
                full_name=repo.full_name,
                source_full_name=repo.source_full_name,
                featured_at=datetime.now(UTC).isoformat(),
                run_id=run_id,
                rank=rank,
            )
            self.data["repositories"].append(asdict(entry))
            current_ids.update(repo.identity_ids)
        self._atomic_write()

    def _atomic_write(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_path = tempfile.mkstemp(prefix="featured-", suffix=".tmp", dir=self.path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(self.data, handle, indent=2, ensure_ascii=False)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_path, self.path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
