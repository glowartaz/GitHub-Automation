import json

import pytest

from github_trending_video.history import FeaturedHistory
from github_trending_video.models import RepoMetadata


def repo(node_id="repo-1", source_node_id="repo-1", full_name="owner/repo"):
    return RepoMetadata(
        node_id=node_id,
        full_name=full_name,
        html_url=f"https://github.com/{full_name}",
        description="",
        owner_login="owner",
        owner_type="User",
        owner_avatar_url="",
        homepage="",
        stars=1,
        forks=0,
        open_issues=0,
        language="Python",
        topics=[],
        license_name="MIT",
        default_branch="main",
        created_at="",
        updated_at="",
        pushed_at="",
        is_fork=source_node_id != node_id,
        source_node_id=source_node_id,
        source_full_name=full_name,
        archived=False,
    )


def test_history_blocks_exact_duplicate(tmp_path):
    history = FeaturedHistory(tmp_path / "history.json")
    history.record([repo()], "2026-08-15")
    reloaded = FeaturedHistory(tmp_path / "history.json")
    assert reloaded.contains(repo(full_name="new-owner/new-name"))


def test_history_blocks_fork_of_featured_source(tmp_path):
    history = FeaturedHistory(tmp_path / "history.json")
    history.record([repo()], "2026-08-15")
    fork = repo(node_id="fork-2", source_node_id="repo-1", full_name="other/fork")
    assert history.contains(fork)


def test_record_rejects_duplicate_in_same_batch(tmp_path):
    history = FeaturedHistory(tmp_path / "history.json")
    with pytest.raises(ValueError, match="Duplicate repository blocked"):
        history.record([repo(), repo(full_name="renamed/repo")], "run")


def test_history_file_is_valid_json(tmp_path):
    path = tmp_path / "history.json"
    FeaturedHistory(path).record([repo()], "run")
    assert json.loads(path.read_text())["repositories"][0]["node_id"] == "repo-1"

