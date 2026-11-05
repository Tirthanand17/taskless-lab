"""B3d4c2c3c: bounded HTTPS-only readback of six primary NASA/NIST/USGS pages.

Only source URLs fixed in the repository may be downloaded, under strict
authority allowlist, TLS, body caps and redirect checks. HTML content is NOT
stored or printed, only full raw/text digests and coarse fact markers.

Coarse keyword matches are NOT independent human fact, rights, originality
or publication approval. Injected mock fetchers can never claim live readback.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
import re
import ssl
import time
from typing import Callable, Mapping
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPSHandler, HTTPRedirectHandler

from autopilot.primary_sourced_storyboards import PRIMARY_REFERENCES,canonical

STATUS="SIX_PUBLIC_PRIMARY_HTML_PAGES_MATCH_COARSE_MARKERS_NO_HUMAN_FACT_APPROVAL"
MAX_HTML=3_000_000
MAX_REDIRECTS=4
MAX_TEXT=1_500_000
AUTHORITY_HOSTS={
    "science.nasa.gov","physics.nist.gov","www.nist.gov",
    "www.usgs.gov","earthquake.usgs.gov",
}
ANCHOR_PATTERNS={
    "nasa_moon":(r"384\s*,\s*400",r"moon"),
    "nist_light":(r"299\s*792\s*458",r"exact"),
    "usgs_magnitude":(r"tenfold increase",r"32 times more energy"),
    "usgs_energy":(r"10\s*\*\*\s*1\.5",r"energy"),
    "nist_binary":(r"1\s+mib",r"1\s+048\s+576",r"8\s+bit"),
    "nist_si":(r"mega",r"million",r"10\s*6"),
}


class SourceReadbackError(ValueError):
    """Source content cannot be accepted or promoted into release."""


def _require_https_authority(url:str) -> str:
    if not isinstance(url,str) or len(url)>250:
        raise SourceReadbackError("Invalid official primary source URL")
    split=urlsplit(url)
    if (split.scheme!="https" or split.hostname not in AUTHORITY_HOSTS
            or split.username is not None or split.password is not None
            or split.port not in (None,443) or split.fragment):
        raise SourceReadbackError("Untrusted primary source URL/redirect")
    return split.hostname


class _OfficialRedirectsOnly(HTTPRedirectHandler):
    def __init__(self):
        super().__init__()
        self.redirects=0

    def redirect_request(self,req,fp,code,msg,headers,newurl):
        self.redirects+=1
        if self.redirects>MAX_REDIRECTS:
            raise SourceReadbackError("Too many third-party redirects")
        _require_https_authority(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)


class _PlainHtml(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip=0
        self.parts=[]

    def handle_starttag(self,tag,attrs):
        if tag in ("script","style","svg"):
            self.skip+=1
        if tag=="img" and not self.skip:
            for k,v in attrs:
                if k=="alt" and isinstance(v,str) and v.strip():
                    self.parts.append(v)

    def handle_endtag(self,tag):
        if tag in ("script","style","svg") and self.skip:
            self.skip-=1

    def handle_data(self,data):
        if not self.skip and data.strip():
            self.parts.append(data)


def _live_fetch(url:str)->tuple[str,str,bytes]:
    _require_https_authority(url)
    redirect=_OfficialRedirectsOnly()
    opener=build_opener(HTTPSHandler(context=ssl.create_default_context()),redirect)
    req=Request(url,headers={
        "User-Agent":"FlowminuteLab-public-primary-source-research/1.0",
        "Accept":"text/html,application/xhtml+xml;q=0.9",
    },method="GET")
    # Unreliable NASA/NIST/USGS upstream TLS response is NOT a failed fact
    # claim. One bounded retry keeps the primary-page gate strict: both
    # attempts must still honor same allowlist, TLS, redirect and body limits;
    # if upstream stays down, DO NOT claim source readback or rights approval.
    for attempt in range(2):
        redirect.redirects=0
        try:
            with opener.open(req,timeout=28) as response:
                final=response.geturl()
                _require_https_authority(final)
                content_type=response.headers.get("Content-Type","").split(";")[0].strip().lower()
                body=response.read(MAX_HTML+1)
                return final,content_type,body
        except SourceReadbackError:
            raise
        except (TimeoutError,OSError) as exc:
            if attempt:
                raise SourceReadbackError("Official HTTPS page inaccessible after bounded retry") from exc
            time.sleep(0.5)
    raise SourceReadbackError("Official HTTPS source unavailable")


def parse_official_page(*,source_id:str,url:str,final_url:str,
                        content_type:str,body:bytes) -> dict:
    if source_id not in PRIMARY_REFERENCES:
        raise SourceReadbackError("Unknown primary scientific source ID")
    if url!=PRIMARY_REFERENCES[source_id]["url"]:
        raise SourceReadbackError("Source URL not pinned in trusted registry")
    hostname=_require_https_authority(url)
    _require_https_authority(final_url)
    if (urlsplit(final_url).hostname!=hostname
            or content_type not in ("text/html","application/xhtml+xml")
            or not isinstance(body,bytes) or not 700<=len(body)<=MAX_HTML):
        raise SourceReadbackError("Wrong page type, size or redirected host")
    try:
        html=body.decode("utf-8",errors="strict")
    except UnicodeDecodeError as exc:
        raise SourceReadbackError("Invalid official HTML text encoding") from exc
    parser=_PlainHtml()
    try:
        parser.feed(html)
    except (ValueError,AssertionError) as exc:
        raise SourceReadbackError("Invalid official page HTML") from exc
    normal=" ".join(" ".join(parser.parts).split()).lower()
    if not 350<=len(normal)<=MAX_TEXT:
        raise SourceReadbackError("Empty or oversized primary text")
    checks=ANCHOR_PATTERNS[source_id]
    if len(checks)<2 or any(re.search(expr,normal,re.IGNORECASE) is None for expr in checks):
        raise SourceReadbackError("Original official page lacks expected coarse fact markers")
    return {
        "source_id":source_id,
        "publisher":PRIMARY_REFERENCES[source_id]["publisher"],
        "fixed_official_url":url,
        "actual_https_final_url":final_url,
        "raw_response_sha256":sha256(body).hexdigest(),
        "visible_extracted_text_sha256":sha256(normal.encode("utf8")).hexdigest(),
        "raw_html_bytes":len(body),
        "all_coarse_public_evidence_markers_present":True,
        "marker_pattern_count":len(checks),
        "full_page_archived_or_licensed":False,
        "meaning_of_all_video_claims_verified":False,
    }


def run_primary_readback(*,fetcher:Callable|None=None,
                         now:datetime|None=None) -> dict:
    """Mock fetcher is for tests and will ALWAYS return MOCK, not LIVE."""
    if now is None:
        now=datetime.now(timezone.utc)
    if (not isinstance(now,datetime) or now.tzinfo is None
            or now.utcoffset() is None):
        raise SourceReadbackError("Public source readback requires aware timestamp")
    scan=[]
    for source_id,ref in PRIMARY_REFERENCES.items():
        url=ref["url"]
        final,kind,body=(_live_fetch(url) if fetcher is None else fetcher(url))
        scan.append(parse_official_page(
            source_id=source_id,url=url,final_url=final,
            content_type=kind,body=body,
        ))
    if len(scan)!=6 or set(x["source_id"] for x in scan)!=set(ANCHOR_PATTERNS):
        raise SourceReadbackError("Missing actual official primary reference")
    live=fetcher is None
    record={
        "schema_version":1,
        "status":STATUS,
        "observed_at_utc":now.astimezone(timezone.utc).isoformat(),
        "method":"LIVE_HTTPS_GET_PUBLIC" if live else "MOCK_INJECTED_HTTP_NO_LIVE_PROOF",
        "official_page_count":len(scan),
        "pages":scan,
        "every_page_coarse_marker_present":True,
        "direct_live_https_readback_completed":live,
        "all_source_claims_independently_human_fact_checked":False,
        "immutable_private_primary_source_archive_connected":False,
        "actual_video_and_metadata_factually_approved":False,
        "real_owner_signed_release":False,
        "youtube_upload_enabled":False,
        "release_authorized":False,
    }
    return {**record,"unapproved_source_readback_packet_sha256":
            sha256(canonical(record)).hexdigest()}


def verify_unapproved_readback(packet:Mapping) -> None:
    """Internal tamper check only; a caller-created digest is NOT trusted."""
    if not isinstance(packet,dict):
        raise SourceReadbackError("Missing primary source packet")
    item={k:v for k,v in packet.items()
          if k!="unapproved_source_readback_packet_sha256"}
    if (sha256(canonical(item)).hexdigest()
            !=packet.get("unapproved_source_readback_packet_sha256")
            or item.get("status")!=STATUS
            or item.get("official_page_count")!=6
            or item.get("release_authorized") is not False
            or item.get("youtube_upload_enabled") is not False
            or item.get("all_source_claims_independently_human_fact_checked") is not False
            or set(x["source_id"] for x in item.get("pages",[]))!=set(PRIMARY_REFERENCES)):
        raise SourceReadbackError("Changed or promoted source readback packet")


def main()->None:
    import json
    packet=run_primary_readback()
    verify_unapproved_readback(packet)
    print("B3D4C2C3C_SIX_LIVE_PUBLIC_PRIMARY_PAGES_COARSE_MARKERS_NOT_FACT_APPROVAL",
          json.dumps(packet,sort_keys=True),flush=True)


if __name__=="__main__":
    main()
