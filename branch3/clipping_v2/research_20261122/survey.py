"""Refresh the public GitHub discovery snapshot (no credentials required)."""
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

QUERIES = [
    'youtube shorts clipping fork:false', '"opus clip" fork:false',
    'topic:ai-clipping fork:false', '"long videos" "shorts" fork:false',
    '"podcast" "highlights" fork:false', 'topic:youtube-shorts-generator fork:false',
    '自动切片 视频 fork:false', '"highlight extraction" video fork:false',
]


def pages(query):
    for number in range(1, 11):
        params = urllib.parse.urlencode(dict(q=query, per_page=100, sort="stars", page=number))
        req = urllib.request.Request("https://api.github.com/search/repositories?" + params,
                                     headers={"User-Agent": "clipping-research"})
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=60) as response:
                    page = json.load(response)
                break
            except urllib.error.HTTPError as exc:
                if exc.code not in (403, 429, 502, 503) or attempt == 2:
                    raise
                time.sleep(61)
        yield page
        if number * 100 >= page["total_count"] or len(page["items"]) < 100:
            break


def main():
    repos, coverage = {}, []
    for query in QUERIES:
        results = list(pages(query))
        found = {r["full_name"]: r for page in results for r in page["items"]}
        coverage.append(dict(query=query, hits=results[0]["total_count"], sampled=len(found),
                             incomplete=any(p["incomplete_results"] for p in results)))
        for repo in found.values():
            key = repo["full_name"]
            if key not in repos:
                repos[key] = dict(url=repo["html_url"], language=repo["language"], stars=repo["stargazers_count"],
                                  license=(repo["license"] or {}).get("spdx_id"),
                                  archived=repo["archived"], pushed_at=repo["pushed_at"], queries=[])
            repos[key]["queries"].append(query)
    result = dict(coverage=coverage, repositories=repos)
    Path(__file__).with_name("inventory.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(len(repos), "distinct results", ascii(coverage))


if __name__ == "__main__":
    main()
