# ~~ES_Aliases:CLI~~
"""
Interactive Elasticsearch maintenance script for Elasticsearch 7.10.2.

Features:
1) List all indices with their alias names.
2) Filter indices that do NOT have any aliases (excluding system indices by default).
3) For each such index, optionally reindex into a new physical index cloned from the original's
   settings and mappings.
4) Optionally delete the original index and then create an alias (with the original index name)
   pointing to the new index.
5) Confirmations are requested per index and before deletion.
6) Generate a JSON report of all actions and outcomes.

Run:
  DOAJENV=dev python portality/scripts/es_reindex_add_aliases.py [--include-system] [--pattern SUBSTR]

Options:
  --include-system     Include indices whose names start with a '.' (system indices). Default: exclude.
  --pattern SUBSTR     Only consider indices whose name contains SUBSTR (useful to scope the operation).
  --dry-run            Do not perform any changes; only show what would happen and create a report.

Notes:
- Requires DOAJ config to connect to ES (ELASTICSEARCH_HOSTS, ELASTIC_SEARCH_VERIFY_CERTS).
- Uses python elasticsearch client compatible with ES 7.10.2.
"""

import os
import json
from copy import deepcopy
from typing import Dict, List, Any

import elasticsearch
from elasticsearch import helpers
from elasticsearch.exceptions import NotFoundError, RequestError, ConnectionError, AuthorizationException

from portality.core import app
from portality.lib.dates import now


def now_ts() -> str:
    return now().strftime("%Y%m%d")


def connect_es() -> elasticsearch.Elasticsearch:
    return elasticsearch.Elasticsearch(
        app.config['ELASTICSEARCH_HOSTS'],
        verify_certs=app.config.get("ELASTIC_SEARCH_VERIFY_CERTS", True),
        timeout=60 * 10,
    )


def get_all_indices(es: elasticsearch.Elasticsearch) -> List[str]:
    # Use _cat/indices for comprehensive listing
    rows = es.cat.indices(format='json')
    indices = [r.get('index') for r in rows if r.get('index')]
    return sorted(indices)


def get_aliases_map(es: elasticsearch.Elasticsearch) -> Dict[str, List[str]]:
    # GET */_alias returns only indices that have aliases
    aliases_map: Dict[str, List[str]] = {}
    try:
        resp = es.indices.get_alias(index="*")
        for index_name, data in resp.items():
            aliases = list((data or {}).get('aliases', {}).keys())
            aliases_map[index_name] = sorted(aliases)
    except NotFoundError:
        # No aliases at all
        pass
    return aliases_map


def clone_index_spec(es: elasticsearch.Elasticsearch, index: str) -> Dict[str, Any]:
    """Fetch settings and mappings for an index and return a sanitized body for index creation."""
    settings_resp = es.indices.get_settings(index=index)
    mapping_resp = es.indices.get_mapping(index=index)

    # Both responses keyed by index
    s = settings_resp[index]['settings']['index']
    m = mapping_resp[index]['mappings']

    # Sanitize settings: remove non-clonable fields
    s = deepcopy(s)
    for k in ['creation_date', 'uuid', 'version', 'provided_name']:  # common non-clonable
        s.pop(k, None)

    body = {
        'settings': {
            'index': s
        },
        'mappings': m
    }
    return body


def prompt_yes_no(question: str, default_no: bool = True) -> bool:
    suffix = "[y/N]" if default_no else "[Y/n]"
    ans = input(f"{question} {suffix} ").strip().lower()
    if ans == 'y' or ans == 'yes':
        return True
    if ans == 'n' or ans == 'no':
        return False
    return not default_no


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Aliasify indices without aliases via reindex.")
    parser.add_argument('--include-system', action='store_true', help='Include indices starting with a dot (system).')
    parser.add_argument('--pattern', default='', help='Only consider indices containing this substring.')
    parser.add_argument('--dry-run', action='store_true', help='Do not change anything; just show plan and report.')
    args = parser.parse_args()

    es = connect_es()

    report = {
        'started_at_utc': now().isoformat() + 'Z',
        'elasticsearch_hosts': app.config.get('ELASTICSEARCH_HOSTS'),
        'include_system': bool(args.include_system),
        'pattern': args.pattern,
        'dry_run': bool(args.dry_run),
        'indices_all': [],              # list of all indices discovered
        'indices_aliases': {},          # index -> [aliases]
        'indices_without_alias': [],
        'skipped_system': [],
        'skipped_pattern': [],
        'processed': [],                # list of per-index reports
        'errors': [],
    }

    try:
        all_indices = get_all_indices(es)
        aliases_map = get_aliases_map(es)
    except Exception as e:
        print(f"Failed to query Elasticsearch: {e}")
        report['errors'].append(f"ES query failure: {e}")
        # Save a minimal report and exit
        _save_report(report)
        return

    report['indices_all'] = all_indices
    # Build index->aliases including empty lists for those without aliases
    indices_aliases_full: Dict[str, List[str]] = {idx: sorted(aliases_map.get(idx, [])) for idx in all_indices}
    report['indices_aliases'] = indices_aliases_full

    # Display list to user
    print("\n== All indices and aliases ==")
    for idx in all_indices:
        aliases = indices_aliases_full.get(idx, [])
        print(f"- {idx} : aliases={aliases if aliases else '[]'}")

    # Compute indices without aliases
    indices_wo_alias = [idx for idx in all_indices if not indices_aliases_full.get(idx)]

    # Filter system and pattern
    candidates: List[str] = []
    for idx in indices_wo_alias:
        if not args.include_system and idx.startswith('.'):
            report['skipped_system'].append(idx)
            continue
        if args.pattern and args.pattern not in idx:
            report['skipped_pattern'].append(idx)
            continue
        candidates.append(idx)

    report['indices_without_alias'] = candidates

    if not candidates:
        print("\nNo indices without aliases match the selection criteria.")
        _save_report(report)
        return

    print("\n== Indices without aliases (candidates) ==")
    for idx in candidates:
        print(f"- {idx}")

    if not prompt_yes_no("Proceed to iterate through these indices?", default_no=True):
        print("Aborted by user.")
        _save_report(report)
        return

    run_ts = now_ts()

    for idx in candidates:
        per = {
            'index': idx,
            'proceeded': False,
            'new_index': None,
            'created_new_index': False,
            'reindex': {
                'attempted': False,
                'result': None,
                'errors_count': 0,
            },
            'delete_original': {
                'prompted': False,
                'deleted': False,
            },
            'alias_created': False,
            'notes': [],
            'exceptions': [],
        }

        if not prompt_yes_no(f"Process index '{idx}'?", default_no=True):
            per['notes'].append('User skipped index')
            report['processed'].append(per)
            continue

        per['proceeded'] = True
        new_index = f"{idx}-{run_ts}"
        per['new_index'] = new_index

        try:
            # Prepare index body
            body = clone_index_spec(es, idx)

            if args.dry_run:
                per['notes'].append('DRY RUN: would create new index and reindex')
            else:
                # Create new index
                if es.indices.exists(index=new_index):
                    per['notes'].append('New index already exists; skipping creation')
                else:
                    es.indices.create(index=new_index, body=body)
                    per['created_new_index'] = True

                # Reindex
                per['reindex']['attempted'] = True
                result, reindex_errors = helpers.reindex(
                    client=es,
                    source_index=idx,
                    target_index=new_index,
                    chunk_size=500,
                )
                per['reindex']['result'] = result
                if reindex_errors:
                    per['reindex']['errors_count'] = len(reindex_errors)
                    per['notes'].append(f"Reindex reported {len(reindex_errors)} errors")

                # Only proceed to delete and alias if reindex had no errors
                reindex_ok = (
                    per['reindex']['errors_count'] == 0
                    and (not isinstance(per['reindex']['result'], dict) or not per['reindex']['result'].get('failures'))
                )

                if not reindex_ok:
                    per['notes'].append("Reindex had errors; skipping delete and alias creation.")
                else:
                    # Prompt deletion of the original index
                    per['delete_original']['prompted'] = True
                    if prompt_yes_no(f"Delete original index '{idx}' now? This cannot be undone.", default_no=True):
                        if args.dry_run:
                            per['notes'].append('DRY RUN: would delete original index')
                        else:
                            es.indices.delete(index=idx)
                            per['delete_original']['deleted'] = True

                    # Create alias pointing original name to new index (works even if original still exists? No, so ensure deleted or choose alt alias)
                    if args.dry_run:
                        per['notes'].append(f"DRY RUN: would create alias '{idx}' -> '{new_index}'")
                    else:
                        # If original still exists, we cannot reuse the same name as alias; require original to be deleted first.
                        if es.indices.exists(index=idx):
                            per['notes'].append("Original index still exists; cannot create alias with same name. Skipping alias creation.")
                        else:
                            es.indices.put_alias(index=new_index, name=idx)
                            per['alias_created'] = True

        except ConnectionError as e:
            msg = f"ConnectionError: {getattr(e, 'info', str(e))}"
            print(msg)
            per['exceptions'].append(msg)
        except NotFoundError as e:
            msg = f"NotFoundError: {getattr(e, 'info', str(e))}"
            print(msg)
            per['exceptions'].append(msg)
        except RequestError as e:
            msg = f"RequestError: {getattr(e, 'info', str(e))}"
            print(msg)
            per['exceptions'].append(msg)
        except AuthorizationException as e:
            msg = f"AuthorizationException: {getattr(e, 'info', str(e))}"
            print(msg)
            per['exceptions'].append(msg)
        except Exception as e:
            msg = f"Unexpected error: {str(e)}"
            print(msg)
            per['exceptions'].append(msg)

        report['processed'].append(per)

    _save_report(report)

    # Final summary
    print("\n== Summary ==")
    total = len(report['processed'])
    done = sum(1 for p in report['processed'] if p['proceeded'])
    deleted = sum(1 for p in report['processed'] if p['delete_original']['deleted'])
    aliased = sum(1 for p in report['processed'] if p['alias_created'])
    print(f"Candidates: {len(candidates)} | Processed: {done} | Deleted original: {deleted} | Aliases created: {aliased}")
    print("Detailed JSON report saved.")


def _save_report(report: Dict[str, Any]) -> None:
    # Ensure reports directory exists
    reports_dir = os.path.join(os.path.dirname(__file__), 'reports')
    os.makedirs(reports_dir, exist_ok=True)
    path = os.path.join(reports_dir, f"es_reindex_add_aliases_{now_ts()}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"Report written to: {path}")


if __name__ == '__main__':
    main()
