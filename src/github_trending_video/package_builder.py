from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from .models import MediaAsset, RepoAnalysis, RepoMetadata


class PackageBuilder:
    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        self.run_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def repo_slug(repo: RepoMetadata) -> str:
        return repo.full_name.lower().replace("/", "--")

    def write_repo(
        self,
        rank: int,
        repo: RepoMetadata,
        analysis: RepoAnalysis,
        assets: list[MediaAsset],
    ) -> Path:
        repo_dir = self.run_dir / "repos" / f"{rank:02d}-{self.repo_slug(repo)}"
        repo_dir.mkdir(parents=True, exist_ok=True)
        payload = {
            "rank": rank,
            "repository": asdict(repo),
            "analysis": analysis.to_dict(),
            "media": [asdict(asset) for asset in assets],
        }
        self._write_json(repo_dir / "research.json", payload)
        (repo_dir / "segment-script.txt").write_text(
            analysis.narration.strip() + "\n", encoding="utf-8"
        )
        return repo_dir

    def write_daily(
        self,
        run_id: str,
        results: list[tuple[RepoMetadata, RepoAnalysis, list[MediaAsset]]],
        warnings: list[str],
    ) -> None:
        summary = {
            "schema_version": 1,
            "run_id": run_id,
            "generated_at": datetime.now(UTC).isoformat(),
            "repository_count": len(results),
            "warnings": warnings,
            "repositories": [
                {
                    "rank": index,
                    "node_id": repo.node_id,
                    "source_node_id": repo.source_node_id,
                    "full_name": repo.full_name,
                    "url": repo.html_url,
                    "summary": analysis.summary,
                    "costs": analysis.costs,
                    "media_count": len(media),
                }
                for index, (repo, analysis, media) in enumerate(results, start=1)
            ],
        }
        self._write_json(self.run_dir / "daily-summary.json", summary)

        titles = [
            f"10 GitHub Repositories You Need to See Today ({run_id})",
            f"GitHub Is Exploding: Today’s Top Open-Source Projects",
            f"The Best New GitHub Projects Trending Right Now",
        ]
        (self.run_dir / "title-options.txt").write_text("\n".join(titles) + "\n", encoding="utf-8")

        script: list[str] = [
            f"# GitHub Trending — {run_id}",
            "",
            "## Opening hook",
            "",
            "Today we’re counting down the GitHub projects developers cannot stop starring. "
            "We checked what each one does, what it takes to run, and what it could cost.",
            "",
        ]
        for countdown, (repo, analysis, _media) in zip(
            range(len(results), 0, -1), results, strict=True
        ):
            script.extend(
                [
                    f"## Number {countdown}: {repo.full_name}",
                    "",
                    analysis.video_hook,
                    "",
                    analysis.narration,
                    "",
                    "Visuals: " + "; ".join(analysis.visual_directions),
                    "",
                ]
            )
        script.extend(
            [
                "## Closing",
                "",
                "Which project should we test in a future video? Links and licensing notes are "
                "in the description. Always review a project before running its code.",
                "",
            ]
        )
        (self.run_dir / "video-script.md").write_text("\n".join(script), encoding="utf-8")
        (self.run_dir / "narration.txt").write_text(
            "\n\n".join(analysis.narration for _, analysis, _ in results) + "\n",
            encoding="utf-8",
        )

        description = [
            f"Top GitHub repositories for {run_id}.",
            "",
            "Repositories featured:",
        ]
        chapters = ["00:00 Today’s GitHub countdown"]
        for index, (repo, _analysis, _media) in enumerate(results, start=1):
            description.append(f"{index}. {repo.full_name} — {repo.html_url}")
            chapters.append(f"TBD Number {len(results) - index + 1}: {repo.full_name}")
        description.extend(
            [
                "",
                "Open-source licenses and external service costs vary. Verify requirements and "
                "pricing with each project or provider before use.",
            ]
        )
        (self.run_dir / "description.md").write_text("\n".join(description) + "\n", encoding="utf-8")
        (self.run_dir / "chapters.txt").write_text("\n".join(chapters) + "\n", encoding="utf-8")
        (self.run_dir / "thumbnail-ideas.md").write_text(
            "# Thumbnail ideas\n\n"
            "- GitHub logo with bold text: **10 PROJECTS EXPLODING**\n"
            "- Three repository screenshots with bold text: **BUILD THESE NOW**\n"
            "- Rising star graph with bold text: **TODAY'S GITHUB WINNERS**\n",
            encoding="utf-8",
        )

    @staticmethod
    def _write_json(path: Path, payload: dict) -> None:
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

