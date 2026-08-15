from __future__ import annotations

import fcntl
import json
import logging
from contextlib import contextmanager
from dataclasses import asdict
from datetime import date
from pathlib import Path
from typing import Iterator

from .analyzer import RepositoryAnalyzer, deterministic_analysis
from .config import Settings
from .github_api import GitHubClient
from .history import FeaturedHistory
from .http import SafeHttpClient
from .media import MediaCollector
from .models import MediaAsset, RepoAnalysis, RepoMetadata
from .package_builder import PackageBuilder
from .trending import TrendingScraper


LOGGER = logging.getLogger(__name__)


@contextmanager
def run_lock(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("Another pipeline run is already active") from exc
        yield


class Pipeline:
    def __init__(self, settings: Settings, no_llm: bool = False, skip_images: bool = False):
        self.settings = settings
        self.no_llm = no_llm
        self.skip_images = skip_images
        if not no_llm and not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required unless --no-llm is used")

    def run(self, run_id: str | None = None, dry_run: bool = False) -> Path:
        run_id = run_id or date.today().isoformat()
        run_dir = self.settings.output_dir / run_id
        lock_path = self.settings.output_dir / ".pipeline.lock"
        with run_lock(lock_path), SafeHttpClient(self.settings.request_timeout_seconds) as http:
            history = FeaturedHistory(self.settings.ledger_path)
            scraper = TrendingScraper(http)
            github = GitHubClient(
                http,
                token=self.settings.github_token,
                max_readme_chars=self.settings.max_readme_chars,
            )
            candidates = scraper.fetch_many(
                self.settings.trending_languages,
                self.settings.candidate_limit,
            )
            selected: list[RepoMetadata] = []
            seen_this_run: set[str] = set()
            warnings: list[str] = []
            for candidate in candidates:
                if len(selected) >= self.settings.max_repos:
                    break
                try:
                    repo = github.fetch_repository(candidate.full_name)
                except Exception as exc:
                    LOGGER.warning("Research skipped for %s: %s", candidate.full_name, exc)
                    continue
                if repo.archived or history.contains(repo) or repo.identity_ids & seen_this_run:
                    continue
                selected.append(repo)
                seen_this_run.update(repo.identity_ids)

            if not selected:
                raise RuntimeError("No unfeatured trending repositories were available")
            if len(selected) < self.settings.max_repos:
                warnings.append(
                    f"Only {len(selected)} unique repositories were available; no duplicates were used."
                )

            analyzer = (
                None
                if self.no_llm
                else RepositoryAnalyzer(self.settings.openai_api_key, self.settings.openai_model)
            )
            collector = MediaCollector(
                http,
                self.settings.image_hosts,
                self.settings.max_images_per_repo,
                self.settings.max_image_bytes,
            )
            builder = PackageBuilder(run_dir)
            results: list[tuple[RepoMetadata, RepoAnalysis, list[MediaAsset]]] = []
            for rank, repo in enumerate(selected, start=1):
                try:
                    analysis = analyzer.analyze(repo) if analyzer else deterministic_analysis(repo)
                    media_dir = run_dir / "repos" / f"{rank:02d}-{builder.repo_slug(repo)}" / "images"
                    media = [] if self.skip_images else collector.download(repo, media_dir)
                    builder.write_repo(rank, repo, analysis, media)
                    results.append((repo, analysis, media))
                except Exception as exc:
                    LOGGER.exception("Packaging failed for %s", repo.full_name)
                    warnings.append(f"{repo.full_name} failed analysis: {type(exc).__name__}")

            if not results:
                raise RuntimeError("All selected repositories failed during analysis")
            builder.write_daily(run_id, results, warnings)
            manifest = {
                "run_id": run_id,
                "dry_run": dry_run,
                "featured_ids": [repo.node_id for repo, _, _ in results],
                "files": sorted(
                    str(path.relative_to(run_dir)) for path in run_dir.rglob("*") if path.is_file()
                ),
            }
            (run_dir / "manifest.json").write_text(
                json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
            )
            if not dry_run:
                history.record([repo for repo, _, _ in results], run_id)
            return run_dir

