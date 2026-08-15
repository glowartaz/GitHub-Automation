from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path


DEFAULT_IMAGE_HOSTS = [
    "github.com",
    "raw.githubusercontent.com",
    "user-images.githubusercontent.com",
    "repository-images.githubusercontent.com",
    "camo.githubusercontent.com",
    "avatars.githubusercontent.com",
]


@dataclass(slots=True)
class Settings:
    max_repos: int = 10
    candidate_limit: int = 60
    trending_languages: list[str] = field(
        default_factory=lambda: ["", "python", "javascript", "typescript", "rust", "go"]
    )
    openai_model: str = "gpt-5-mini"
    max_readme_chars: int = 50_000
    max_images_per_repo: int = 6
    max_image_bytes: int = 8_000_000
    request_timeout_seconds: float = 20.0
    image_hosts: list[str] = field(default_factory=lambda: list(DEFAULT_IMAGE_HOSTS))
    output_dir: Path = Path("output")
    ledger_path: Path = Path("data/featured-repos.json")
    github_token: str = ""
    openai_api_key: str = ""

    @classmethod
    def load(cls, config_path: str | None = None) -> "Settings":
        raw: dict = {}
        if config_path:
            raw = json.loads(Path(config_path).read_text(encoding="utf-8"))
        settings = cls(**{k: v for k, v in raw.items() if hasattr(cls, k)})
        settings.github_token = os.getenv("GITHUB_TOKEN", settings.github_token)
        settings.openai_api_key = os.getenv("OPENAI_API_KEY", settings.openai_api_key)
        settings.openai_model = os.getenv("OPENAI_MODEL", settings.openai_model)
        if os.getenv("MAX_REPOS"):
            settings.max_repos = int(os.environ["MAX_REPOS"])
        if os.getenv("TRENDING_LANGUAGES"):
            settings.trending_languages = [
                x.strip() for x in os.environ["TRENDING_LANGUAGES"].split(",")
            ]
        settings.output_dir = Path(settings.output_dir)
        settings.ledger_path = Path(settings.ledger_path)
        settings.validate()
        return settings

    def validate(self) -> None:
        if not 1 <= self.max_repos <= 25:
            raise ValueError("max_repos must be between 1 and 25")
        if not self.max_repos <= self.candidate_limit <= 100:
            raise ValueError("candidate_limit must be between max_repos and 100")
        if self.max_readme_chars > 200_000:
            raise ValueError("max_readme_chars must not exceed 200000")
        if self.max_images_per_repo > 12:
            raise ValueError("max_images_per_repo must not exceed 12")
