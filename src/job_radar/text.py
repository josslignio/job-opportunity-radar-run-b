from __future__ import annotations

from html import unescape
from html.parser import HTMLParser
import re
import unicodedata


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        text = data.strip()
        if text:
            self.parts.append(text)


def html_to_text(value: str | None) -> str:
    if not value:
        return ""
    parser = _TextExtractor()
    parser.feed(unescape(str(value)))
    return normalize_space(" ".join(parser.parts))


def normalize_space(value: str | None) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def fold(value: str | None) -> str:
    normalized = unicodedata.normalize("NFKD", normalize_space(value).lower())
    return "".join(ch for ch in normalized if not unicodedata.combining(ch))


def contains_term(text: str, term: str) -> bool:
    return fold(term) in fold(text)
