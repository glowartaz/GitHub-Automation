from __future__ import annotations

import hashlib
import html
import mimetypes
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse

from .http import SafeHttpClient
from .models import MediaAsset, RepoMetadata


MARKDOWN_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^\s)]+)(?:\s+[^)]*)?\)")
HTML_IMAGE = re.compile(r"<img\b[^>]*?\bsrc=[\"']([^\"']+)[\"'][^>]*>", re.IGNORECASE)
ALT_ATTRIBUTE = re.compile(r"\balt=[\"']([^\"']*)[\"']", re.IGNORECASE)


class MediaCollector:
    def __init__(
        self,
        http: SafeHttpClient,
        allowed_hosts: list[str],
        max_images: int,
        max_bytes: int,
    ):
        self.http = http
        self.allowed_hosts = {host.lower() for host in allowed_hosts}
        self.max_images = max_images
        self.max_bytes = max_bytes

    def _allowed(self, url: str) -> bool:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        return parsed.scheme == "https" and host in self.allowed_hosts and not parsed.username

    @staticmethod
    def _resolve(repo: RepoMetadata, url: str) -> str:
        url = html.unescape(url.strip("<>"))
        if url.startswith("//"):
            return "https:" + url
        if url.startswith("http://") or url.startswith("https://"):
            return url
        raw_base = (
            f"https://raw.githubusercontent.com/{repo.full_name}/{repo.default_branch}/"
        )
        return urljoin(raw_base, url)

    def discover(self, repo: RepoMetadata) -> list[tuple[str, str]]:
        discovered: list[tuple[str, str]] = []
        for match in MARKDOWN_IMAGE.finditer(repo.readme_text):
            discovered.append((self._resolve(repo, match.group(2)), match.group(1)))
        for match in HTML_IMAGE.finditer(repo.readme_text):
            tag = match.group(0)
            alt = ALT_ATTRIBUTE.search(tag)
            discovered.append((self._resolve(repo, match.group(1)), alt.group(1) if alt else ""))
        if repo.owner_avatar_url:
            discovered.append((repo.owner_avatar_url, f"{repo.owner_login} avatar"))
        unique: list[tuple[str, str]] = []
        seen: set[str] = set()
        for url, alt in discovered:
            normalized = url.split("#", 1)[0]
            if normalized not in seen and self._allowed(normalized):
                unique.append((normalized, alt))
                seen.add(normalized)
        return unique[: self.max_images]

    def download(self, repo: RepoMetadata, target_dir: Path) -> list[MediaAsset]:
        target_dir.mkdir(parents=True, exist_ok=True)
        assets: list[MediaAsset] = []
        for index, (url, alt) in enumerate(self.discover(repo), start=1):
            try:
                with self.http.client.stream(
                    "GET", url, headers={"Accept": "image/*"}
                ) as response:
                    response.raise_for_status()
                    if not self._allowed(str(response.url)):
                        continue
                    content_type = response.headers.get("content-type", "").split(";", 1)[0]
                    declared_size = int(response.headers.get("content-length") or 0)
                    if not content_type.startswith("image/") or declared_size > self.max_bytes:
                        continue
                    chunks: list[bytes] = []
                    size = 0
                    for chunk in response.iter_bytes():
                        size += len(chunk)
                        if size > self.max_bytes:
                            chunks = []
                            break
                        chunks.append(chunk)
                    content = b"".join(chunks)
                    if not content:
                        continue
                extension = mimetypes.guess_extension(content_type) or Path(urlparse(url).path).suffix
                if extension not in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}:
                    extension = ".img"
                digest = hashlib.sha256(url.encode()).hexdigest()[:10]
                path = target_dir / f"{index:02d}-{digest}{extension}"
                path.write_bytes(content)
                assets.append(
                    MediaAsset(
                        source_url=url,
                        local_path=str(path),
                        media_type=content_type,
                        alt_text=alt,
                        attribution=f"Source: {repo.full_name} README or GitHub profile",
                    )
                )
            except Exception:
                continue
        return assets
