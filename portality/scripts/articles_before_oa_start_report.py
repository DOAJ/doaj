"""
Generate a CSV report of all articles in the index that appear to be published earlier than
their journal's Open Access (OA) start year.

How it works
- For each Article, find its associated Journal using the Article model's helper.
- Read the Journal's OA start year via Journal.has_oa_start_date().
- Compare the Article's publication year (bibjson.year) to the OA start year.
- If article_year < oa_start_year, output a row in the CSV.

Usage examples
    DOAJENV=<environment> python portality/scripts/articles_before_oa_start_report.py -o before_oa_start.csv \
      --page-size 1000 --keepalive 10m --retries 10 --retry-wait 5

Notes
- Articles without a resolvable Journal or without a numeric year are skipped.
- Journals without an OA start year are skipped.
- The script only reads from the index and does not modify any data.
"""

import csv
import sys
import time
from typing import Iterable, Optional, List, Dict, Tuple, Iterator

from portality.lib import dates
from portality.models import Article, Journal
from portality.models.article import ArticleQuery
from portality.dao import ScrollTimeoutException


HEADERS = [
    "Article ID",
    "Article Title",
    "Article Year",
    "eISSN",
    "pISSN",
    "Journal ID",
    "Journal Title",
    "Journal OA Start Year",
]


def _safe_int(val: Optional[str]) -> Optional[int]:
    try:
        if val is None:
            return None
        return int(str(val))
    except Exception:
        return None


def article_generator(issns: Optional[List[str]] = None, page_size: int = 1000, keepalive: str = "10m") -> Iterable[Article]:
    """Yield Article domain objects, optionally filtered by ISSNs. Excludes withdrawn articles."""
    if issns:
        query = ArticleQuery(issns=issns, in_doaj=True).query()
    else:
        query = ArticleQuery(in_doaj=True).query()
    for a in Article.iterate(q=query, page_size=page_size, keepalive=keepalive, wrap=True):
        yield a


def iter_articles_raw_for_issns(issns: List[str], page_size: int = 1000, keepalive: str = "10m") -> Iterator[dict]:
    """Yield raw article _source dicts for the given ISSNs, excluding withdrawn, with minimal _source."""
    must = [
        {"term": {"admin.in_doaj": True}},
        {"exists": {"field": "bibjson.year"}},
        {"terms": {"index.issn.exact": issns}},
    ]
    q = {
        "query": {"bool": {"must": must}},
        "_source": [
            "id",
            "bibjson.year",
            "bibjson.title",
            "bibjson.identifier",
            "index.issn.exact",
        ],
        "track_total_hits": True,
    }
    for hit in Article.iterate(q=q, page_size=page_size, keepalive=keepalive, wrap=False):
        yield hit


def retrying_article_src_stream(issns: List[str], page_size: int = 1000, keepalive: str = "10m",
                                retries: int = 10, retry_wait: int = 5) -> Iterator[dict]:
    """Yield raw article _source dicts, restarting the ES scroll on ScrollTimeoutException up to `retries` times."""
    attempt = 0
    while True:
        try:
            for src in iter_articles_raw_for_issns(issns=issns, page_size=page_size, keepalive=keepalive):
                yield src
            return
        except ScrollTimeoutException as e:
            attempt += 1
            if attempt > retries:
                print(f"Scroll timed out repeatedly; giving up after {retries} retries. Last error: {e}", file=sys.stderr)
                raise
            print(f"Scroll context lost (attempt {attempt}/{retries}). Waiting {retry_wait}s then retrying a fresh scan...", file=sys.stderr)
            time.sleep(retry_wait)
            # loop and restart a fresh iterator


def build_issn_to_journal_map(page_size: int = 2000, keepalive: str = "10m") -> Dict[str, Tuple[str, str, int]]:
    """Build a map of ISSN → (journal_id, journal_title, oa_start_year) for journals in DOAJ with an OA start year."""
    must = [
        {"term": {"admin.in_doaj": True}},
        {"exists": {"field": "bibjson.oa_start"}},
    ]
    q = {
        "query": {"bool": {"must": must}},
        "_source": [
            "id",
            "bibjson.title",
            "bibjson.pissn",
            "bibjson.eissn",
            "bibjson.oa_start",
        ],
        "track_total_hits": True,
    }
    issn_map: Dict[str, Tuple[str, str, int]] = {}
    for jsrc in Journal.iterate(q=q, page_size=page_size, keepalive=keepalive, wrap=False):
        bj = jsrc.get("bibjson", {})
        oa = _safe_int(bj.get("oa_start"))
        if oa is None:
            continue
        jid = jsrc.get("id")
        jtitle = bj.get("title", "")
        for issn in [bj.get("pissn"), bj.get("eissn")]:
            if issn:
                issn_map[str(issn)] = (jid, jtitle, oa)
    return issn_map


def _chunked(iterable: List[str], size: int) -> Iterator[List[str]]:
    for i in range(0, len(iterable), size):
        yield iterable[i:i + size]


def make_row_from_hit(src: dict, issn_map: Dict[str, Tuple[str, str, int]]):
    # article fields
    bj = src.get("bibjson", {})
    title = bj.get("title") or ""
    year = _safe_int(bj.get("year"))
    if year is None:
        return None

    # ISSNs on the article (indexed convenience field)
    issns = []
    index_part = src.get("index", {})
    issn_part = index_part.get("issn", {})
    if isinstance(issn_part, dict):
        issns = issn_part.get("exact", []) or []
    elif isinstance(issn_part, list):
        issns = issn_part

    # also look at identifiers in bibjson if needed
    pissn = None
    eissn = None
    idents = bj.get("identifier") or []
    if isinstance(idents, list):
        for ident in idents:
            if ident.get("type") == "pissn" and not pissn:
                pissn = ident.get("id")
            if ident.get("type") == "eissn" and not eissn:
                eissn = ident.get("id")
    # prefer indexed field for matching
    candidate_issns = issns or [i for i in [pissn, eissn] if i]
    match = next((i for i in candidate_issns if i in issn_map), None)
    if not match:
        return None

    jid, jtitle, oa_start = issn_map[match]
    if year < oa_start:
        # Resolve final pissn/eissn nicely for output
        out_p = pissn
        out_e = eissn
        return {
            "Article ID": src.get("id", ""),
            "Article Title": title,
            "Article Year": str(year),
            "eISSN": out_e or "",
            "pISSN": out_p or "",
            "Journal ID": jid,
            "Journal Title": jtitle or "",
            "Journal OA Start Year": str(oa_start),
        }
    return None


def run(out_file: str,
        issns: Optional[List[str]] = None,
        limit: Optional[int] = None,
        page_size: int = 1000,
        keepalive: str = "10m",
        retries: int = 10,
        retry_wait: int = 5,
        flush_every: int = 1000):

    count_examined = 0
    count_flagged = 0

    # Build journal ISSN → (journal_id, title, oa_start)
    issn_map = build_issn_to_journal_map(page_size=2000, keepalive=keepalive)
    if not issn_map:
        print("No journals with OA start found; nothing to do.", file=sys.stderr)

    # If user provided ISSNs, restrict to those that exist in the journal map
    issn_list = list(issn_map.keys()) if not issns else [i for i in issns if i in issn_map]
    if issns and not issn_list:
        print("Provided ISSNs do not match any journals with OA start; exiting.", file=sys.stderr)

    with open(out_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADERS)

        written_since_flush = 0

        CHUNK = 5000  # issn terms chunk size to keep query manageable
        chunk_index = 0
        total_chunks = (len(issn_list) // CHUNK) + (1 if len(issn_list) % CHUNK else 0)

        for issn_chunk in _chunked(issn_list, CHUNK):
            chunk_index += 1
            print(f"Processing ISSN chunk {chunk_index}/{total_chunks} containing {len(issn_chunk)} ISSNs", file=sys.stderr)

            for src in retrying_article_src_stream(issns=issn_chunk, page_size=page_size, keepalive=keepalive,
                                                   retries=retries, retry_wait=retry_wait):
                count_examined += 1

                row = make_row_from_hit(src, issn_map)
                if row is not None:
                    writer.writerow([row[h] for h in HEADERS])
                    count_flagged += 1
                    written_since_flush += 1

                if written_since_flush >= flush_every:
                    f.flush()
                    written_since_flush = 0

                if limit is not None and count_examined >= limit:
                    break

                # Simple progress to stderr every 10k records
                if count_examined % 10000 == 0:
                    print(f"Scanned {count_examined} articles; flagged {count_flagged} so far...", file=sys.stderr)

            if limit is not None and count_examined >= limit:
                break

        # final flush to ensure content hits disk
        f.flush()

    print(f"Done. Examined {count_examined} articles; flagged {count_flagged}. Output: {out_file}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Report articles earlier than their journal's OA start year")
    parser.add_argument("-o", "--out", help="Output CSV file path", default=f"articles_before_oa_start_{dates.today()}.csv")
    parser.add_argument("-n", "--limit", type=int, help="Limit number of articles to scan (for testing)")
    parser.add_argument("-s", "--issn", action="append", help="Restrict scan to these ISSNs (may be supplied multiple times)")
    parser.add_argument("-p", "--page-size", type=int, default=1000, help="Scroll page size for ES iterate")
    parser.add_argument("-k", "--keepalive", default="10m", help="Elasticsearch scroll keepalive, e.g. 10m")
    parser.add_argument("-r", "--retries", type=int, default=10, help="Retries on scroll timeout")
    parser.add_argument("-w", "--retry-wait", type=int, default=5, help="Seconds to wait between retries")
    parser.add_argument("--flush-every", type=int, default=1000, help="Flush output to disk every N rows")

    args = parser.parse_args()

    run(out_file=args.out,
        issns=args.issn,
        limit=args.limit,
        page_size=args.page_size,
        keepalive=args.keepalive,
        retries=args.retries,
        retry_wait=args.retry_wait,
        flush_every=args.flush_every)
