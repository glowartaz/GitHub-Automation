from github_trending_video.media import MediaCollector
from github_trending_video.models import RepoMetadata


def repo(readme):
    return RepoMetadata(
        node_id="1",
        full_name="owner/repo",
        html_url="https://github.com/owner/repo",
        description="",
        owner_login="owner",
        owner_type="User",
        owner_avatar_url="https://avatars.githubusercontent.com/u/1",
        homepage="",
        stars=0,
        forks=0,
        open_issues=0,
        language="",
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
        readme_text=readme,
    )


def test_discover_resolves_relative_and_rejects_unknown_hosts():
    collector = MediaCollector(
        http=None,
        allowed_hosts=["raw.githubusercontent.com", "avatars.githubusercontent.com"],
        max_images=6,
        max_bytes=1000,
    )
    assets = collector.discover(
        repo("![Demo](docs/demo.png)\n![Bad](https://untrusted.example/tracker.png)")
    )
    urls = [url for url, _ in assets]
    assert "https://raw.githubusercontent.com/owner/repo/main/docs/demo.png" in urls
    assert not any("untrusted.example" in url for url in urls)


def test_only_https_is_allowed():
    collector = MediaCollector(None, ["raw.githubusercontent.com"], 6, 1000)
    assert not collector._allowed("http://raw.githubusercontent.com/file.png")
    assert collector._allowed("https://raw.githubusercontent.com/file.png")

