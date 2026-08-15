from __future__ import annotations

import time

import httpx


class SafeHttpClient:
    def __init__(self, timeout: float = 20.0, headers: dict[str, str] | None = None):
        base_headers = {
            "User-Agent": "github-trending-video/0.1 (+research automation)",
            "Accept": "text/html,application/json;q=0.9,*/*;q=0.8",
        }
        base_headers.update(headers or {})
        self.client = httpx.Client(
            timeout=timeout,
            headers=base_headers,
            follow_redirects=True,
            max_redirects=3,
        )

    def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        last_error: Exception | None = None
        for attempt in range(3):
            try:
                response = self.client.request(method, url, **kwargs)
                if response.status_code in {429, 500, 502, 503, 504} and attempt < 2:
                    time.sleep(2**attempt)
                    continue
                response.raise_for_status()
                return response
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                last_error = exc
                if attempt < 2:
                    time.sleep(2**attempt)
                    continue
                raise
        raise RuntimeError(f"Request failed: {url}") from last_error

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "SafeHttpClient":
        return self

    def __exit__(self, *_args) -> None:
        self.close()
