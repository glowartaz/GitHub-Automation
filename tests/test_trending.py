from github_trending_video.trending import TrendingScraper


HTML = """
<article class="Box-row">
  <h2><a href="/example/project"> example / project </a></h2>
  <p>A useful project</p>
  <span itemprop="programmingLanguage">Python</span>
  <span>1,234 stars today</span>
</article>
"""


def test_parse_trending_repository():
    items = TrendingScraper.parse(HTML)
    assert len(items) == 1
    assert items[0].full_name == "example/project"
    assert items[0].stars_today == 1234
    assert items[0].language == "Python"


def test_empty_trending_page_fails_closed():
    try:
        TrendingScraper.parse("<html></html>")
    except RuntimeError as exc:
        assert "no repositories" in str(exc)
    else:
        raise AssertionError("Expected parser failure")

