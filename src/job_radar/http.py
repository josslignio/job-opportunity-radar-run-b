from __future__ import annotations

import json
import socket
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


class NetworkDisabled(RuntimeError):
    pass


class FetchError(RuntimeError):
    pass


ALLOWED_HOSTS = {
    "boards-api.greenhouse.io",
    "api.lever.co",
    "api.eu.lever.co",
    "api.ashbyhq.com",
}


def get_json(url: str, *, allow_network: bool, timeout: float = 20.0,
             retries: int = 2, max_bytes: int = 10_000_000) -> object:
    if not allow_network:
        raise NetworkDisabled("Network access requires --allow-network")
    parsed = urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise FetchError(f"Blocked host or scheme: {url}")
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "JOSS-Job-Opportunity-Radar/0.1 (+manual-first)",
        },
        method="GET",
    )
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                length = response.headers.get("Content-Length")
                if length and int(length) > max_bytes:
                    raise FetchError(f"Response too large: {length} bytes")
                body = response.read(max_bytes + 1)
                if len(body) > max_bytes:
                    raise FetchError(f"Response exceeded {max_bytes} bytes")
                charset = response.headers.get_content_charset() or "utf-8"
                return json.loads(body.decode(charset))
        except (HTTPError, URLError, socket.timeout, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt >= retries:
                break
            time.sleep(0.5 * (2 ** attempt))
    raise FetchError(f"GET failed after {retries + 1} attempts: {url}: {last_error}")
