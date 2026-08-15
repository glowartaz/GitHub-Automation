from __future__ import annotations

import re
from urllib.parse import quote

from bs4 import BeautifulSoup

from .http import SafeHttpClient
from .models import TrendingCandidate


def _number(text: str) -> int:
    match = re.search(r"([\d,]+)", text)
    return int(match.group(1).replace(",", "")) if match else 0


class TrendingScraper:
    BASE_URL = "https://github.com/trending"

    def __init__(self, http: SafeHttpClient):
        self.http = http

    def fetch(self, language: str = "") -> list[TrendingCandidate]:
        url = self.BASE_URL + (f"/{quote(language)}" if language else "") + "?since=daily"
        html = self.http.request("GET", url).text
        return self.parse(html)

    @staticmethod
    def parse(html: str) -> list[TrendingCandidate]:
        soup = BeautifulSoup(html, "html.parser")
        candidates: list[TrendingCandidate] = []
        for rank, article in enumerate(soup.select("article.Box-row"), start=1):
            heading = article.select_one("h2 a")
            if not heading:
                continue
            full_name = "".join(heading.stripped_strings).replace(" ", "")
            full_name = full_name.strip("/")
            if full_name.count("/") != 1:
                continue
            description_node = article.select_one("p")
            language_node = article.select_one("[itemprop='programmingLanguage']")
            stars_today_node = next(
                (x for x in article.select("span") if "stars today" in x.get_text(" ", strip=True)),
                None,
            )
            candidates.append(
                TrendingCandidate(
                    full_name=full_name,
                    url=f"https://github.com/{full_name}",
                    description=description_node.get_text(" ", strip=True)
                    if description_node
                    else "",
                    language=language_node.get_text(strip=True) if language_node else "",
                    stars_today=_number(stars_today_node.get_text(" ", strip=True))
                    if stars_today_node
                    else 0,
                    trending_rank=rank,
                )
            )
        if not candidates:
            raise RuntimeError("GitHub Trending markup returned no repositories")
        return candidates

    def fetch_many(self, languages: list[str], limit: int) -> list[TrendingCandidate]:
        combined: dict[str, TrendingCandidate] = {}
        for language in languages or [""]:
            for candidate in self.fetch(language):
                current = combined.get(candidate.full_name.lower())
                if current is None or candidate.stars_today > current.stars_today:
                    combined[candidate.full_name.lower()] = candidate
                if len(combined) >= limit:
                    break
        return sorted(
            combined.values(),
            key=lambda item: (-item.stars_today, item.trending_rank, item.full_name.lower()),
        )[:limit]

