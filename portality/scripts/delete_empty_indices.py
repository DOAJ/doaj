#!/usr/bin/env python3
# ~~DeleteEmptyIndices:CLI~~
"""
Script to delete Elasticsearch indices that have 0 documents.
This helps clean up empty indices that may have been created but never used.

This is mainly of use for test servers with duplicated indexes, of which one is used.

Run:
  DOAJENV=dev python portality/scripts/delete_empty_indices.py [--dry-run] [--exclude PATTERN ...]

Options:
  --dry-run            List empty indices without deleting them
  --exclude PATTERN    Index patterns to exclude from deletion (can be specified multiple times)
                       Default excludes: .kibana, .security, .monitoring, .apm, .tasks
  --include-system     Include system indices (those starting with '.')
  --keep-latest        Keep the latest empty index for each prefix (based on timestamp in name)

Notes:
- Requires DOAJ config to connect to ES (ELASTICSEARCH_HOSTS, ELASTIC_SEARCH_VERIFY_CERTS)
- Uses the es_connection singleton from portality.core
- Prompts for confirmation before deleting unless --yes flag is provided
"""

import argparse
import sys
from typing import List, Dict
from collections import defaultdict

from portality.core import app, es_connection


DEFAULT_EXCLUDES = ['.kibana', '.security', '.monitoring', '.apm', '.tasks', '.watches']


def get_all_indices() -> List[Dict]:
    """Get list of all indices with their document counts from Elasticsearch."""
    try:
        # Use _cat/indices to get index stats including doc count
        indices = es_connection.cat.indices(format='json')
        return indices
    except Exception as e:
        print(f'Error fetching indices: {e}', file=sys.stderr)
        sys.exit(1)


def extract_index_prefix(index_name: str) -> str:
    """
    Extract the prefix from an index name, removing the timestamp suffix.

    For example: 'doaj-ur_review_route-20251126_172410_000655' -> 'doaj-ur_review_route'

    Args:
        index_name: Full index name with timestamp

    Returns:
        Index prefix without timestamp
    """
    # Split by hyphen and look for the timestamp pattern (YYYYMMDD_HHMMSS_microseconds)
    parts = index_name.split('-')
    if len(parts) < 2:
        return index_name

    # Check if the last part looks like a timestamp (starts with 8 digits)
    last_part = parts[-1]
    if len(last_part) >= 8 and last_part[:8].isdigit():
        # Return everything except the last part (timestamp)
        return '-'.join(parts[:-1])

    return index_name


def find_empty_indices(indices: List[Dict], exclude_patterns: List[str], include_system: bool, keep_latest: bool) -> List[Dict]:
    """
    Filter indices that have 0 documents.

    Args:
        indices: List of index dicts from ES
        exclude_patterns: Patterns to exclude from results
        include_system: Whether to include system indices (starting with '.')
        keep_latest: Whether to keep the latest empty index for each prefix

    Returns:
        List of empty index dicts with name, size, status, and health
    """
    empty_indices = []

    for idx in indices:
        index_name = idx.get('index', '')
        doc_count = int(idx.get('docs.count', 0))

        # Skip if not 0 documents
        if doc_count != 0:
            continue

        # Skip system indices unless explicitly included
        if not include_system and index_name.startswith('.'):
            continue

        # Skip if matches any exclude pattern
        excluded = False
        for pattern in exclude_patterns:
            if pattern in index_name or index_name.startswith(pattern):
                excluded = True
                break

        if not excluded:
            empty_indices.append({
                'name': index_name,
                'size': idx.get('store.size', '0b'),
                'status': idx.get('status', 'unknown'),
                'health': idx.get('health', 'unknown'),
                'docs_deleted': idx.get('docs.deleted', '0')
            })

    # If keep_latest is enabled, filter out all but the latest index for each prefix
    if keep_latest and empty_indices:
        # Group indices by prefix
        prefix_groups = defaultdict(list)
        for idx in empty_indices:
            prefix = extract_index_prefix(idx['name'])
            prefix_groups[prefix].append(idx)

        # For each prefix, keep only the latest (sorted by name, which includes timestamp)
        indices_to_delete = []
        for prefix, group in prefix_groups.items():
            # Sort by name (descending) - latest timestamp will be first
            sorted_group = sorted(group, key=lambda x: x['name'], reverse=True)
            # Keep the first (latest), add the rest to delete list
            indices_to_delete.extend(sorted_group[1:])

        return indices_to_delete

    return empty_indices


def delete_index(index_name: str) -> tuple:
    """
    Delete a specific index.

    Returns:
        Tuple of (success: bool, message: str)
    """
    try:
        resp = es_connection.indices.delete(index=index_name)
        return True, f"Deleted successfully: {resp}"
    except Exception as e:
        return False, str(e)


def main():
    parser = argparse.ArgumentParser(
        description='Delete empty Elasticsearch indices (indices with 0 documents)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='List empty indices without deleting them'
    )
    parser.add_argument(
        '--exclude',
        nargs='*',
        default=[],
        help='Additional index patterns to exclude from deletion'
    )
    parser.add_argument(
        '--include-system',
        action='store_true',
        help='Include system indices (those starting with ".")'
    )
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Skip confirmation prompt and proceed with deletion'
    )
    parser.add_argument(
        '--keep-latest',
        action='store_true',
        help='Keep the latest empty index for each prefix (based on timestamp in name)'
    )

    args = parser.parse_args()

    # Build exclude list
    exclude_patterns = DEFAULT_EXCLUDES + args.exclude

    print(f'Connecting to Elasticsearch at {app.config["ELASTICSEARCH_HOSTS"]}...')

    # Test connection
    try:
        cluster_info = es_connection.info()
        print(f'Connected to Elasticsearch {cluster_info["version"]["number"]}')
    except Exception as e:
        print(f'Failed to connect to Elasticsearch: {e}', file=sys.stderr)
        sys.exit(1)

    # Get all indices
    all_indices = get_all_indices()
    print(f'Total indices found: {len(all_indices)}')

    # Find empty indices
    empty_indices = find_empty_indices(all_indices, exclude_patterns, args.include_system, args.keep_latest)

    if not empty_indices:
        if args.keep_latest:
            print('\nNo empty indices to delete (keeping latest for each prefix).')
        else:
            print('\nNo empty indices found.')
        return

    if args.keep_latest:
        print(f'\nFound {len(empty_indices)} empty indices to delete (keeping latest for each prefix):')
    else:
        print(f'\nFound {len(empty_indices)} empty indices:')
    print(f'{"Index Name":<60} {"Size":<10} {"Health":<10} {"Status":<10}')
    print('-' * 90)
    for idx in empty_indices:
        print(f'{idx["name"]:<60} {idx["size"]:<10} {idx["health"]:<10} {idx["status"]:<10}')

    if args.dry_run:
        print('\n[DRY RUN] No indices were deleted.')
        if args.keep_latest:
            print('Note: With --keep-latest flag, the latest empty index for each prefix would be kept.')
        print(f'\nTo delete these indices, run without --dry-run flag.')
        return

    # Confirm deletion
    print(f'\nAbout to delete {len(empty_indices)} empty indices.')
    print(f'Excluded patterns: {", ".join(exclude_patterns)}')
    if args.keep_latest:
        print('Keep latest: Enabled (will preserve the most recent empty index for each prefix)')

    if not args.yes:
        confirmation = input('\nContinue with deletion? (yes/no): ')
        if confirmation.lower() not in ['yes', 'y']:
            print('Cancelled.')
            return

    # Delete indices
    print('\nDeleting empty indices...')
    success_count = 0
    error_count = 0

    for idx in empty_indices:
        index_name = idx['name']
        success, message = delete_index(index_name)

        if success:
            print(f'  ✓ Deleted: {index_name}')
            success_count += 1
        else:
            print(f'  ✗ Failed to delete {index_name}: {message}')
            error_count += 1

    print(f'\n{"=" * 50}')
    print(f'Summary:')
    print(f'  Successfully deleted: {success_count}')
    print(f'  Failed: {error_count}')
    print(f'{"=" * 50}')


if __name__ == '__main__':
    main()
