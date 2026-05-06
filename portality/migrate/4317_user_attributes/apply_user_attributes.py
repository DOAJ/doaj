"""Migration script to add user attributes (country and language) based on Editor Group CSVs.

Usage:
    python -m portality.migrate.4317_user_attributes /path/to/countries.csv /path/to/languages.csv

The first CSV should have two columns with headers: the first is the country name, the second the Editor Group name.
The second CSV should have two columns with headers: the first is the language name, the second the Editor Group name.

For each row this script finds the EditorGroup by name, collects the accounts attached to the group
(maned, editor, associates) and schedules the appropriate ISO code to be added to each user's attributes
('country' or 'language'). All validations are done against the portality datasets (pycountry/isolang).

The script collates all labels for each user and performs a single save per user at the end.
"""

import csv
import sys
import argparse
from collections import defaultdict

from portality.models.editors import EditorGroup
from portality.models.account import Account
from portality import datasets, constants
from portality.lib import isolang
from portality.core import app


def resolve_country_code(name: str):
    """Return a 2-character country code for a given country name, or None if not found."""
    if not name:
        return None
    code = datasets.get_country_code(name, fail_if_not_found=True)
    return code


def resolve_language_code(name: str):
    """Return a 2-character language code (alpha2) for a given language name, or None if not found."""
    if not name:
        return None
    lang = isolang.find(name)
    if not lang:
        return None
    # isolang.find returns a dict with 'alpha2' key
    return lang.get('alpha2')


def read_pairs_from_csv(path):
    """Read CSV and return list of (label, editor_group_name) pairs using the first two columns.

    Expects two columns with headers; will take the first and second header values.
    """
    pairs = []
    with open(path, newline='') as fh:
        reader = csv.DictReader(fh)
        headers = reader.fieldnames
        if not headers or len(headers) < 2:
            raise ValueError(f"CSV at {path} must have at least two columns with headers")
        col_label = headers[0]
        col_group = headers[1]
        for row in reader:
            label = (row.get(col_label) or '').strip()
            group = (row.get(col_group) or '').strip()
            if label and group:
                pairs.append((label, group))
    return pairs


def collate_attributes(country_pairs, language_pairs):
    """Process pairs and collate desired attributes per account id.

    Returns mapping: account_id -> { 'country': set(...), 'language': set(...) }
    """
    account_attrs = defaultdict(lambda: {'country': set(), 'language': set()})

    def _collect_for_group(group_name, code, attr_type):
        eg = EditorGroup.group_by_name(group_name)
        if eg is None:
            app.logger.warning(f"EditorGroup not found: '{group_name}'")
            print(f"WARNING: EditorGroup not found: '{group_name}'")
            return

        # collect maned, editor, associates
        acct_ids = set()
        if eg.maned:
            acct_ids.add(eg.maned)
        if eg.editor:
            acct_ids.add(eg.editor)
        for a in eg.associates or []:
            acct_ids.add(a)

        for aid in acct_ids:
            if not aid:
                continue
            account_attrs[aid][attr_type].add(code)

    # countries
    for country_name, group_name in country_pairs:
        code = resolve_country_code(country_name)
        if code is None:
            app.logger.warning(f"Unable to resolve country '{country_name}'")
            print(f"WARNING: Unable to resolve country '{country_name}'")
            continue
        _collect_for_group(group_name, code.upper(), 'country')

    # languages
    for lang_name, group_name in language_pairs:
        code = resolve_language_code(lang_name)
        if code is None:
            app.logger.warning(f"Unable to resolve language '{lang_name}'")
            print(f"WARNING: Unable to resolve language '{lang_name}'")
            continue
        _collect_for_group(group_name, code.upper(), 'language')

    return account_attrs


def apply_attributes(account_attrs, dry_run=False):
    """Apply collated attributes to Account objects and save them once each.

    Returns a summary dict.
    """
    summary = {'updated': 0, 'skipped_missing_account': 0}
    for aid, attrs in account_attrs.items():
        acc = Account.pull(aid)
        if acc is None:
            summary['skipped_missing_account'] += 1
            app.logger.warning(f"Account not found: {aid}")
            print(f"WARNING: Account not found: {aid}")
            continue

        changed = False
        # countries
        for c in sorted(attrs.get('country', [])):
            try:
                if not acc.has_attribute(constants.USER_ATTR__COUNTRY, c):
                    acc.add_attribute(constants.USER_ATTR__COUNTRY, c)
                    changed = True
            except Exception:
                app.logger.exception(f"Failed to add country attribute '{c}' to account {aid}")

        for l in sorted(attrs.get('language', [])):
            try:
                if not acc.has_attribute(constants.USER_ATTR__LANGUAGE, l):
                    acc.add_attribute(constants.USER_ATTR__LANGUAGE, l)
                    changed = True
            except Exception:
                app.logger.exception(f"Failed to add language attribute '{l}' to account {aid}")

        if changed:
            if dry_run:
                print(f"DRY RUN: Would save account {aid} with new attributes: {attrs}")
            else:
                acc.save()
                print(f"Saved account {aid} (added {len(attrs.get('country', []))} country(s), {len(attrs.get('language', []))} language(s))")
            summary['updated'] += 1

    return summary


def main():
    parser = argparse.ArgumentParser(description='Add user attributes from Editor Group CSVs')
    parser.add_argument('countries_csv', help='CSV: first col country name, second col Editor Group name')
    parser.add_argument('languages_csv', help='CSV: first col language name, second col Editor Group name')
    parser.add_argument('--dry-run', action='store_true', help='Do not save changes, just report')

    args = parser.parse_args()

    country_pairs = read_pairs_from_csv(args.countries_csv)
    language_pairs = read_pairs_from_csv(args.languages_csv)

    print(f"Read {len(country_pairs)} country rows and {len(language_pairs)} language rows")

    account_attrs = collate_attributes(country_pairs, language_pairs)

    print(f"Collated attributes for {len(account_attrs)} accounts")

    summary = apply_attributes(account_attrs, dry_run=args.dry_run)

    print("Done. Summary:")
    print(summary)


if __name__ == '__main__':
    main()

