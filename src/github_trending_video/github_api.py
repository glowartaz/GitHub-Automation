from __future__ import annotations

import base64
from typing import Any
from urllib.parse import quote

from .http import SafeHttpClient
from .models import RepoMetadata


class GitHubClient:
    API = "https://api.github.com"
    INTERESTING_FILES = [
        ".env.example",
        "package.json",
        "pyproject.toml",
        "requirements.txt",
        "docker-compose.yml",
        "compose.yml",
        "Dockerfile",
        "LICENSE",
    ]

    def __init__(self, http: SafeHttpClient, token: str = "", max_readme_chars: int = 50_000):
        self.http = http
        self.max_readme_chars = max_readme_chars
        self.headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def _get(self, path: str, optional: bool = False) -> Any:
        try:
            return self.http.request("GET", f"{self.API}{path}", headers=self.headers).json()
        except Exception:
            if optional:
                return None
            raise

    @staticmethod
    def _decode_content(payload: dict | None, limit: int) -> str:
        if not payload or payload.get("encoding") != "base64":
            return ""
        try:
            return base64.b64decode(payload.get("content", ""), validate=False).decode(
                "utf-8", errors="replace"
            )[:limit]
        except (ValueError, TypeError):
            return ""

    def fetch_repository(self, full_name: str) -> RepoMetadata:
        safe_name = "/".join(quote(part, safe="") for part in full_name.split("/"))
        repo = self._get(f"/repos/{safe_name}")
        if not repo or not repo.get("node_id"):
            raise RuntimeError(f"Repository metadata missing for {full_name}")

        source = repo.get("source") or repo.get("parent") or {}
        readme = self._get(f"/repos/{safe_name}/readme", optional=True)
        owner = self._get(f"/users/{quote(repo['owner']['login'], safe='')}", optional=True) or {}
        release = self._get(f"/repos/{safe_name}/releases/latest", optional=True) or {}

        notable_files: dict[str, str] = {}
        for file_name in self.INTERESTING_FILES:
            payload = self._get(
                f"/repos/{safe_name}/contents/{quote(file_name, safe='')}", optional=True
            )
            content = self._decode_content(payload, 12_000)
            if content:
                notable_files[file_name] = content

        return RepoMetadata(
            node_id=repo["node_id"],
            full_name=repo["full_name"],
            html_url=repo["html_url"],
            description=repo.get("description") or "",
            owner_login=repo["owner"]["login"],
            owner_type=repo["owner"].get("type") or "",
            owner_avatar_url=repo["owner"].get("avatar_url") or "",
            homepage=repo.get("homepage") or "",
            stars=int(repo.get("stargazers_count") or 0),
            forks=int(repo.get("forks_count") or 0),
            open_issues=int(repo.get("open_issues_count") or 0),
            language=repo.get("language") or "",
            topics=repo.get("topics") or [],
            license_name=(repo.get("license") or {}).get("spdx_id") or "Not detected",
            default_branch=repo.get("default_branch") or "main",
            created_at=repo.get("created_at") or "",
            updated_at=repo.get("updated_at") or "",
            pushed_at=repo.get("pushed_at") or "",
            is_fork=bool(repo.get("fork")),
            source_node_id=source.get("node_id") or repo["node_id"],
            source_full_name=source.get("full_name") or repo["full_name"],
            archived=bool(repo.get("archived")),
            readme_text=self._decode_content(readme, self.max_readme_chars),
            readme_html_url=(readme or {}).get("html_url") or "",
            owner_bio=owner.get("bio") or "",
            owner_blog=owner.get("blog") or "",
            owner_company=owner.get("company") or "",
            latest_release=release.get("tag_name") or "",
            notable_files=notable_files,
        )

