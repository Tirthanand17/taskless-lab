"""Unprivileged cloud topic scout. No credentials, video creation or publishing.

RSS/Atom headlines are *leads*, NEVER verified facts or permission to publish.
A separate researcher must read sources and independently confirm each claim.
"""
from __future__ import annotations
import argparse
import datetime as dt
import email.utils
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, asdict
from pathlib import Path

FEEDS = (
    ("OpenAI", "https://openai.com/news/rss.xml"),
    ("Google DeepMind", "https://deepmind.google/blog/rss.xml"),
    ("The Verge", "https://www.theverge.com/rss/index.xml"),
)
KEYWORDS = (" ai ", "agent", "gemini", "openai", "chatgpt", "claude",
            "data", "automation", "spreadsheet", "coding", "model")
MIN_SOURCE_COUNT = 2
UTC = dt.timezone.utc

@dataclass(frozen=True)
class Lead:
    publisher: str
    title: str
    url: str
    published_utc: str
    relevance: float
    status: str = "unverified_lead"

def _date(raw: str) -> dt.datetime | None:
    if not raw: return None
    try:
        d = email.utils.parsedate_to_datetime(raw)
    except (ValueError, TypeError):
        try: d = dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError: return None
    if d.tzinfo is None: d = d.replace(tzinfo=UTC)
    return d.astimezone(UTC)

def _find_text(node: ET.Element, names: tuple[str, ...]) -> str:
    for child in node.iter():
        if child.tag.split("}")[-1] in names and child.text and child.text.strip():
            return child.text.strip()
    return ""

def _article_link(item: ET.Element) -> str:
    for node in item:
        if node.tag.split("}")[-1] != "link": continue
        link = node.attrib.get("href") or node.text or ""
        if link.strip().startswith("https://"): return link.strip()
    return ""

def extract(xml: str, publisher: str, now: dt.datetime, max_age_hours: int = 96,
            existing_titles: tuple[str, ...] = ()) -> list[Lead]:
    root = ET.fromstring(xml)
    items = [n for n in root.iter() if n.tag.split("}")[-1] in ("item", "entry")]
    out: list[Lead] = []
    for item in items:
        title = _find_text(item, ("title",))
        link = _article_link(item)
        published = _date(_find_text(item, ("pubDate", "published", "updated")))
        if not title or not link or published is None: continue
        if not 0 <= (now - published).total_seconds() <= max_age_hours * 3600: continue
        if not any(k in (" " + title.lower() + " ") for k in KEYWORDS): continue
        if any(_jaccard(title, old) > .63 for old in existing_titles): continue
        freshness = 1 - (now - published).total_seconds() / (max_age_hours * 3600)
        out.append(Lead(publisher, title, link, published.isoformat(), round(.4 + .6 * freshness, 3)))
    return out

def _jaccard(a: str, b: str) -> float:
    toks = lambda text: set(re.findall(r"[a-z0-9]+", text.lower())) - {"the","a","for","with","in","to","and"}
    x, y = toks(a), toks(b)
    return len(x & y) / len(x | y) if x | y else 0

def fetch_feed(url: str, timeout_s: int = 15) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.username:
        raise ValueError("HTTPS-only feed required")
    allowed = {urllib.parse.urlparse(x[1]).hostname for x in FEEDS}
    if parsed.hostname not in allowed: raise ValueError("Feed origin not allowlisted")
    req = urllib.request.Request(url, headers={"User-Agent": "FlowMinutePublicResearch/1.0"})
    with urllib.request.urlopen(req, timeout=timeout_s) as response:
        final = urllib.parse.urlparse(response.url)
        if final.scheme != "https" or final.hostname not in allowed:
            raise ValueError("Feed redirected outside allowlist")
        body = response.read(1_048_577)
        if len(body) > 1_048_576: raise ValueError("Feed unexpectedly large")
        return body.decode("utf-8-sig")

def scout(now: dt.datetime | None = None, existing_titles: tuple[str,...] = ()) -> dict:
    now = now or dt.datetime.now(UTC)
    if now.tzinfo is None: raise ValueError("Timezone aware now required")
    leads: list[Lead] = []
    errors = []
    for publisher, feed in FEEDS:
        try:
            leads.extend(extract(fetch_feed(feed), publisher, now, existing_titles=existing_titles))
        except (OSError, ET.ParseError, UnicodeError, ValueError, TimeoutError) as ex:
            errors.append({"publisher": publisher, "error_type": type(ex).__name__})
    leads.sort(key=lambda x: -x.relevance)
    return {
        "generated_at_utc": now.astimezone(UTC).isoformat(),
        "status": "leads_only_no_publish_authorization",
        "independent_feeds_checked": len(FEEDS),
        "independent_feeds_with_leads": len({x.publisher for x in leads}),
        "minimum_independent_publishers_for_fact_check": MIN_SOURCE_COUNT,
        "leads": [asdict(x) for x in leads[:24]],
        "errors": errors,
        "next_step": "Manually or with an approved researcher verify source claims; this report alone never authorizes scripts, rendering, or upload."
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", default="out/scout-report.json")
    args=p.parse_args()
    report=scout()
    out=Path(args.output)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(json.dumps({"status":report["status"],"lead_count":len(report["leads"]),"errors":len(report["errors"])}))

if __name__ == "__main__": main()
