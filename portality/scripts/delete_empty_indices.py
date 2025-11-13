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

Notes:
- Requires DOAJ config to connect to ES (ELASTICSEARCH_HOSTS, ELASTIC_SEARCH_VERIFY_CERTS)
- Uses the es_connection singleton from portality.core
- Prompts for confirmation before deleting unless --yes flag is provided
"""

import argparse
import sys
from typing import List, Dict

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


def find_empty_indices(indices: List[Dict], exclude_patterns: List[str], include_system: bool) -> List[Dict]:
    """
    Filter indices that have 0 documents.

    Args:
        indices: List of index dicts from ES
        exclude_patterns: Patterns to exclude from results
        include_system: Whether to include system indices (starting with '.')

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
    empty_indices = find_empty_indices(all_indices, exclude_patterns, args.include_system)

    if not empty_indices:
        print('\nNo empty indices found.')
        return

    print(f'\nFound {len(empty_indices)} empty indices:')
    print(f'{"Index Name":<60} {"Size":<10} {"Health":<10} {"Status":<10}')
    print('-' * 90)
    for idx in empty_indices:
        print(f'{idx["name"]:<60} {idx["size"]:<10} {idx["health"]:<10} {idx["status"]:<10}')

    if args.dry_run:
        print('\n[DRY RUN] No indices were deleted.')
        print(f'\nTo delete these indices, run without --dry-run flag.')
        return

    # Confirm deletion
    print(f'\nAbout to delete {len(empty_indices)} empty indices.')
    print(f'Excluded patterns: {", ".join(exclude_patterns)}')

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
