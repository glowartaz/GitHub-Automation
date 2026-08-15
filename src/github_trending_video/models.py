from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class TrendingCandidate:
    full_name: str
    url: str
    description: str = ""
    language: str = ""
    stars_today: int = 0
    trending_rank: int = 0


@dataclass(slots=True)
class RepoMetadata:
    node_id: str
    full_name: str
    html_url: str
    description: str
    owner_login: str
    owner_type: str
    owner_avatar_url: str
    homepage: str
    stars: int
    forks: int
    open_issues: int
    language: str
    topics: list[str]
    license_name: str
    default_branch: str
    created_at: str
    updated_at: str
    pushed_at: str
    is_fork: bool
    source_node_id: str
    source_full_name: str
    archived: bool
    readme_text: str = ""
    readme_html_url: str = ""
    owner_bio: str = ""
    owner_blog: str = ""
    owner_company: str = ""
    latest_release: str = ""
    notable_files: dict[str, str] = field(default_factory=dict)

    @property
    def identity_ids(self) -> set[str]:
        return {value for value in (self.node_id, self.source_node_id) if value}


@dataclass(slots=True)
class MediaAsset:
    source_url: str
    local_path: str
    media_type: str
    alt_text: str = ""
    license_status: str = "review-required"
    attribution: str = ""


@dataclass(slots=True)
class RepoAnalysis:
    summary: str
    how_it_works: str
    best_for: list[str]
    setup_steps: list[str]
    requirements: list[str]
    applications_and_skills: list[str]
    integrations: list[str]
    costs: list[dict[str, str]]
    creator_highlights: list[str]
    cautions: list[str]
    video_hook: str
    narration: str
    visual_directions: list[str]
    confidence_notes: list[str]
    source_urls: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

