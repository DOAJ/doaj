# This file builds a set of records from which to restore notes data by incremental analysis

#!/usr/bin/env python3
"""
Read a CSV with two columns (type, id) and for each row fetch the document from a local
Elasticsearch instance and write it to a directory named after the id as `base.json`.

Usage:
    python build_restore_base.py input.csv

Options:
    --es-host HOST     Elasticsearch host (default: localhost)
    --es-port PORT     Elasticsearch port (default: 9200)
    --out-dir DIR      Base output directory (default: current working directory)

CSV format:
    The CSV must have a header row which will be skipped. Each subsequent row must have
    two columns: the first is either 'Journal' or 'Application' and the second is the id.

The script will create one directory per id under the output directory and write a
`base.json` file containing the JSON returned from Elasticsearch for that document.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import os
import sys
import time
import random
from typing import Dict, Optional

try:
    import requests
except Exception:
    requests = None  # If requests isn't available, we'll error later with a helpful message


INDEX_MAP: Dict[str, str] = {
    "Journal": "-doaj-journal-20250822_ascii_folding",
    "Application": "-doaj-application-20250822_ascii_folding",
}

INDEX_START = 14
INDEX_END = 27


def fetch_document(es_host: str, es_port: int, index: str, doc_id: str, timeout: int = 10,
                   max_retries: int = 5, backoff_factor: float = 0.5, max_backoff: float = 60.0):
    """Fetch a document from Elasticsearch using the _doc endpoint with retries on 429 and
    transient network errors.

    This function will:
    - retry when Elasticsearch responds with HTTP 429 (Too Many Requests), using the
      Retry-After header when present, otherwise exponential backoff with jitter;
    - optionally retry on transient network errors (requests.exceptions.RequestException);
    - return the final requests.Response on success (including 200 or 404), or raise the
      last encountered RequestException if all retries fail due to network errors.

    Parameters:
        es_host, es_port, index, doc_id: used to build the request URL
        timeout: per-request timeout in seconds
        max_retries: number of attempts (including the initial attempt)
        backoff_factor: base backoff in seconds used for exponential backoff
        max_backoff: maximum sleep between retries
    """
    if requests is None:
        raise RuntimeError("The 'requests' library is required. Install it with: pip install requests")

    url = f"http://{es_host}:{es_port}/{index}/_doc/{doc_id}"

    last_exc: Optional[Exception] = None
    last_resp: Optional["requests.Response"] = None

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.get(url, timeout=timeout)
            last_resp = resp

            # If not a 429, return the response directly (may be 200, 404, 5xx, etc.)
            if resp.status_code != 429:
                return resp

            # Handle 429: respect Retry-After header if present
            retry_after = None
            if "Retry-After" in resp.headers:
                try:
                    retry_after = int(resp.headers.get("Retry-After"))
                except Exception:
                    # Could be a HTTP-date; ignore and fall back to exponential backoff
                    retry_after = None

            if retry_after is not None:
                sleep_for = min(float(retry_after), max_backoff)
            else:
                # exponential backoff with jitter
                sleep_for = min(backoff_factor * (2 ** (attempt - 1)), max_backoff)
                # add small jitter up to 20%
                jitter = random.uniform(0, sleep_for * 0.2)
                sleep_for = sleep_for + jitter

            # If this was the last attempt, break and return the 429 response
            if attempt == max_retries:
                break

            time.sleep(sleep_for)
            continue

        except requests.exceptions.RequestException as e:
            # Treat as transient network error: retry with backoff unless out of attempts
            last_exc = e
            if attempt == max_retries:
                break

            sleep_for = min(backoff_factor * (2 ** (attempt - 1)), max_backoff)
            jitter = random.uniform(0, sleep_for * 0.2)
            time.sleep(sleep_for + jitter)
            continue

    # If we get here, either we've exhausted retries for 429 (return last_resp) or for
    # network errors (raise last_exc). Prefer returning the last response if present.
    if last_resp is not None:
        return last_resp
    if last_exc is not None:
        raise last_exc

    # Fallback: should not be reached
    raise RuntimeError("Failed to fetch document and no response or exception recorded")


def write_base_json(output_dir: str, filename: str, content: dict):
    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, filename)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(content, fh, indent=2, ensure_ascii=False)


def process_csv(csv_path: str, es_host: str, es_port: int, out_base: str):
    errors = 0
    processed = 0

    with open(csv_path, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.reader(csvfile)
        header = next(reader, None)  # skip header
        for rownum, row in enumerate(reader, start=2):
            if not row:
                logging.debug("Skipping empty row %s", rownum)
                continue
            if len(row) < 2:
                logging.warning("Row %s has fewer than 2 columns, skipping: %r", rownum, row)
                errors += 1
                continue

            typ = row[0].strip()
            if typ == "Application":
                continue # skipping for the moment
            doc_id = row[1].strip()
            if not doc_id:
                logging.warning("Row %s has empty id, skipping", rownum)
                errors += 1
                continue

            base_index = INDEX_MAP.get(typ)
            if base_index is None:
                logging.warning("Unknown type '%s' on row %s, skipping", typ, rownum)
                errors += 1
                continue

            outfile = "base.json"
            for index_prefix in range(INDEX_START, INDEX_END):
                index = str(index_prefix) + base_index

                logging.info("Fetching %s (id=%s) from index %s", typ, doc_id, index)
                try:
                    time.sleep(0.5)
                    resp = fetch_document(es_host, es_port, index, doc_id)
                except Exception as e:
                    logging.error("Network error fetching id %s (row %s): %s", doc_id, rownum, e)
                    errors += 1
                    break

                if resp.status_code == 200:
                    try:
                        data = resp.json()
                    except ValueError:
                        logging.error("Invalid JSON response for id %s (row %s)", doc_id, rownum)
                        errors += 1
                        break

                    # Write only the document _source into base.json. If _source is missing
                    # log an error and skip this document.
                    source = data.get("_source")
                    if source is None:
                        logging.error("No _source found in ES response for id %s (row %s)", doc_id, rownum)
                        errors += 1
                        break

                    out_dir = os.path.join(out_base, typ, doc_id)
                    outfile = "base_" + str(index_prefix) + ".json"
                    write_base_json(out_dir, outfile, source)
                    processed += 1
                    logging.info("Wrote %s/%s", out_dir, outfile)
                    if typ == "Journal":
                        break  # we just need a baseline journal record, we can stop here
                    # if Application, we still try further indexes as we want all records

                elif resp.status_code == 404:
                    logging.warning("Document not found for id %s (row %s): 404", doc_id, rownum)
                    errors += 1
                    # here we increment the index prefix and try the next index
                    continue
                else:
                    # log body (may be helpful for ES errors)
                    text = resp.text[:1000] if resp.text else ""
                    logging.error(
                        "Failed to fetch id %s (row %s): status=%s, body=%s",
                        doc_id,
                        rownum,
                        resp.status_code,
                        text,
                    )
                    errors += 1
                    break  # don't try further indexes for this doc_id




    logging.info("Done. Processed=%d, Errors=%d", processed, errors)
    return processed, errors


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build base.json files by fetching docs from Elasticsearch")
    parser.add_argument("csv", help="Path to input CSV (header row will be skipped)")
    parser.add_argument("--es-host", default=os.environ.get("ES_HOST", "localhost"), help="Elasticsearch host (default: localhost or $ES_HOST)")
    parser.add_argument("--es-port", type=int, default=int(os.environ.get("ES_PORT", "9200")), help="Elasticsearch port (default: 9200 or $ES_PORT)")
    parser.add_argument("--out-dir", default=os.getcwd(), help="Base output directory (default: current working directory)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose logging")

    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s: %(message)s",
    )

    if requests is None:
        logging.error("The 'requests' package is required. Install it with: pip install requests")
        sys.exit(2)

    csv_path = args.csv
    if not os.path.exists(csv_path):
        logging.error("CSV file does not exist: %s", csv_path)
        sys.exit(2)

    processed, errors = process_csv(csv_path, args.es_host, args.es_port, args.out_dir)
    if errors:
        logging.warning("Completed with errors: %d errors", errors)
        sys.exit(1)
    else:
        logging.info("Completed successfully: %d documents written", processed)
        sys.exit(0)


if __name__ == "__main__":
    main()
