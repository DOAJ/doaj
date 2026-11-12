import logging
from copy import deepcopy

from portality.models import Article

logger = logging.getLogger(__name__)


def _transform_authors(authors):
    """
    Transform a list of authors from old affiliation format to new affiliations format.

    Returns a tuple of (merged_authors, had_old_format, had_duplicates) where:
    - merged_authors: the transformed list of authors
    - had_old_format: True if any author had old-style 'affiliation' string
    - had_duplicates: True if any duplicate authors were merged
    """
    had_old_format = False
    had_duplicates = False

    # First pass: convert old "affiliation" string to "affiliations" list
    for author in authors:
        if "affiliation" in author:
            had_old_format = True
            affiliation = author.pop("affiliation")
            if affiliation:
                existing = author.get("affiliations", [])
                if affiliation not in existing:
                    existing.append(affiliation)
                author["affiliations"] = existing

    # Second pass: merge duplicate authors by name
    merged = []
    seen = {}  # name -> index in merged list

    for author in authors:
        name = author.get("name", "")
        if name in seen:
            had_duplicates = True
            # Merge affiliations into existing author entry
            idx = seen[name]
            existing_affiliations = merged[idx].get("affiliations", [])
            for aff in author.get("affiliations", []):
                if aff not in existing_affiliations:
                    existing_affiliations.append(aff)
            if existing_affiliations:
                merged[idx]["affiliations"] = existing_affiliations

            # Preserve orcid_id if the existing entry doesn't have one
            if "orcid_id" not in merged[idx] and "orcid_id" in author:
                merged[idx]["orcid_id"] = author["orcid_id"]
        else:
            seen[name] = len(merged)
            merged.append(author)

    return merged, had_old_format, had_duplicates


def _log_author_changes(article_id, old_authors, new_authors, had_old_format, had_duplicates):
    """Log the changes."""
    updated_type = "Old Format" if had_old_format else "Duplicate author" if had_duplicates else None

    logger.info("Article %s updated %s", article_id, updated_type)
    logger.info("  Old authors (%d):", len(old_authors))

    for a in old_authors:
        aff = a.get("affiliation", "")
        affs = a.get("affiliations", [])
        aff_display = aff if aff else ("; ".join(affs) if affs else "none")
        aff_name = "affiliation" if aff else "affiliations"
        logger.info("    - %s | %s: %s", a.get("name", "Unknown"), aff_name, aff_display)
    logger.info("  New authors (%d):", len(new_authors))
    for a in new_authors:
        affs = a.get("affiliations", [])
        aff_display = "; ".join(affs) if affs else "none"
        logger.info("    - %s | affiliations: %s", a.get("name", "Unknown"), aff_display)


def migrate_affiliations(source: dict, dryrun=False):
    """
    Migrate article authors from old affiliation format to new affiliations format.

    Old format: each author has a single "affiliation" string, and an author with multiple
    affiliations appears as duplicate entries with different affiliation values.

    New format: each author appears once with an "affiliations" list containing all their
    affiliations.

    This function:
    1. Converts any "affiliation" (string) to "affiliations" (list)
    2. Merges duplicate authors (by name) into a single entry with combined affiliations
    """
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    bj = source.get("bibjson", {})
    old_authors = bj.get("author", [])

    if not old_authors:
        return Article(**source)

    article_id = source.get("id", "unknown")
    old_authors_snapshot = deepcopy(old_authors)

    merged, had_old_format, had_duplicates = _transform_authors(old_authors)

    if had_old_format or had_duplicates:
        _log_author_changes(article_id, old_authors_snapshot, merged, had_old_format, had_duplicates)

    if dryrun:
        return merged, had_old_format, had_duplicates

    bj["author"] = merged

    return Article(**source)
