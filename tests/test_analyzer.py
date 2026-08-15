from github_trending_video.analyzer import deterministic_analysis
from github_trending_video.models import RepoMetadata


def test_fallback_detects_common_requirements():
    repo = RepoMetadata(
        node_id="1",
        full_name="owner/repo",
        html_url="https://github.com/owner/repo",
        description="Example",
        owner_login="owner",
        owner_type="User",
        owner_avatar_url="",
        homepage="",
        stars=0,
        forks=0,
        open_issues=0,
        language="Python",
        topics=[],
        license_name="MIT",
        default_branch="main",
        created_at="",
        updated_at="",
        pushed_at="",
        is_fork=False,
        source_node_id="1",
        source_full_name="owner/repo",
        archived=False,
        readme_text="Install with Python. Copy .env and add your API key. Docker is supported.",
    )
    analysis = deterministic_analysis(repo)
    assert "Python" in analysis.requirements
    assert "Docker" in analysis.requirements
    assert "API key or environment configuration" in analysis.requirements

