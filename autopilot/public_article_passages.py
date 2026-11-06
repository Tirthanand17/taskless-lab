"""B4d7 minimal in-memory source passages for editorial claim investigation.

A complete page body was ALREADY read by the exact-host bounded source probe.
No second HTTP request, scraping outside allowlisted publishers, large source
cache, AI calls, license assertion, factual endorsement or YouTube upload.

Only at most TWO literal <=140-character fragments per verified article are
temporarily held on the GitHub runner. They are deleted after evidence docket
generation, NEVER printed or included in public GitHub Actions artifacts.
"""
from __future__ import annotations

from hashlib import sha256
from html.parser import HTMLParser
import re

PASSAGE_STATUS = "EPHEMERAL_LITERAL_SOURCE_PASSAGES_NEED_FACT_AND_RIGHTS_REVIEW"
MAX_PASSAGES_PER_SOURCE = 2
MAX_CHARS_PER_PASSAGE = 140
MAX_PARAGRAPHS_EXAMINED = 80
BLOCKED_TAGS = frozenset(("script","style","noscript","nav","footer",
                          "header","aside","form","button","svg","iframe"))
BLOCKED_PHRASES = frozenset((
    "cookie policy","privacy policy","all rights reserved",
    "subscribe now","sign in to", "advertisement", "javascript is disabled",
    "enable javascript","your browser", "accept cookies",
))
SECRET_PATTERNS = re.compile(
    r"(?:https?://|www\.|\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b|"
    r"\b(?:api[_ -]?key|access[_ -]?token|password|secret|bearer)\b)",
    re.IGNORECASE,
)


class _LimitedParagraphs(HTMLParser):
    """Only visible p/abstract blockquotes; never script, nav, or metadata."""
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.skip_tags: list[str] = []
        self.active_tag: str | None = None
        self.chunks: list[str] = []
        self.paragraphs: list[str] = []

    def _finish(self) -> None:
        if self.active_tag is not None:
            txt = " ".join(" ".join(self.chunks).split())
            if txt:
                self.paragraphs.append(txt[:2000])
        self.active_tag = None
        self.chunks = []

    def handle_starttag(self, tag, attrs):
        if tag in BLOCKED_TAGS:
            self.skip_tags.append(tag)
        if self.skip_tags:
            return
        if tag in ("p","blockquote") and self.active_tag is None:
            self.active_tag = tag
            self.chunks = []
        elif tag in ("br",) and self.active_tag is not None:
            self.chunks.append(" ")

    def handle_endtag(self, tag):
        if self.skip_tags:
            if tag == self.skip_tags[-1]:
                self.skip_tags.pop()
            return
        if self.active_tag == tag:
            self._finish()

    def handle_data(self, data):
        if self.active_tag is not None and not self.skip_tags:
            self.chunks.append(data[:3000])

    def close(self):
        super().close()
        self._finish()


def _clean_literal(txt: str) -> str | None:
    text = " ".join(txt.split())
    if len(text) < 75 or SECRET_PATTERNS.search(text):
        return None
    if any(s in text.lower() for s in BLOCKED_PHRASES):
        return None
    # Fixed character cap, cut at a word boundary, not copy full paragraphs.
    snippet = text[:MAX_CHARS_PER_PASSAGE]
    if len(text) > MAX_CHARS_PER_PASSAGE:
        snippet = snippet.rsplit(" ", 1)[0]
    if not 60 <= len(snippet) <= MAX_CHARS_PER_PASSAGE:
        return None
    if any(ord(c) < 32 for c in snippet):
        return None
    return snippet


def extract_literal_passages(page: bytes, mime: str) -> list[dict]:
    """Hash a tiny exact source-text fragment; do NOT infer a factual claim."""
    if not isinstance(page, bytes) or not 96 <= len(page) <= 1_048_576:
        raise ValueError("Source bytes must be explicitly bounded")
    if mime not in ("text/html", "application/xhtml+xml",
                    "text/plain", "text/xml", "application/xml"):
        raise ValueError("Unsupported public textual source type")
    text = page.decode("utf8", errors="replace")
    if mime in ("text/html", "application/xhtml+xml"):
        reader = _LimitedParagraphs()
        reader.feed(text)
        reader.close()
        paragraphs = reader.paragraphs[:MAX_PARAGRAPHS_EXAMINED]
    elif mime == "text/plain":
        paragraphs = text.splitlines()[:MAX_PARAGRAPHS_EXAMINED]
    else:
        # XML text isn't reliably an article paragraph. Fail closed.
        paragraphs = []
    selected = []
    seen = set()
    for index, paragraph in enumerate(paragraphs):
        snippet = _clean_literal(paragraph)
        if snippet is None or snippet.casefold() in seen:
            continue
        seen.add(snippet.casefold())
        selected.append({
            "passage_index": index,
            "literal_excerpt_unverified": snippet,
            "literal_excerpt_sha256": sha256(snippet.encode("utf8")).hexdigest(),
            "not_a_semantic_claim_or_fact_review": True,
            "not_licensed_for_narration_or_public_reuse": True,
        })
        if len(selected) >= MAX_PASSAGES_PER_SOURCE:
            break
    return selected
