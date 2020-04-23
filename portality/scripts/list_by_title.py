import csv
import re
from copy import deepcopy
import esprit
import string
from portality.core import app
from portality import models
from unidecode import unidecode

INPUT = "/home/richard/tmp/doaj/titlematch.csv"
OUT = "/home/richard/tmp/doaj/matchedtitles-live.csv"


APPS_NOT_ACCEPTED = {
    "query" : {
        "bool" : {
            "must_not" : [
                {"term" : {"admin.application_status" : "accepted"}}
            ]
        }
    },
    "sort" : [{"index.unpunctitle.exact" : {"order" : "asc"}}]
}


ALL_JOURNALS = {
    "query" : {
        "match_all" : {}
    }
}


def list_by_title(input, out):
    # first read in and prep the search data
    terms = _prep_search_terms(input)

    conn = esprit.raw.make_connection(None, app.config["ELASTIC_SEARCH_HOST"], None,
                                      app.config["ELASTIC_SEARCH_DB"])

    application_rows = []
    for a in esprit.tasks.scroll(conn, models.Suggestion.__type__, q=APPS_NOT_ACCEPTED, page_size=1000, keepalive='5m'):
        application = models.Suggestion(_source=a)
        title = application.bibjson().title
        alt = application.bibjson().alternative_title
        titles = []
        if title is not None and title != "":
            titles.append(_normalise_title(title))
        if alt is not None and alt != "":
            titles.append(_normalise_title(alt))
        for variants in terms:
            for v in variants:
                if v in titles or len([t for t in titles if v in t]) > 0:
                    row = [variants[-1]] + _extract_report_row(application)
                    application_rows.append(row)
                    break

    journal_rows = []
    for j in esprit.tasks.scroll(conn, models.Journal.__type__, q=ALL_JOURNALS, page_size=1000, keepalive='5m'):
        journal = models.Journal(_source=j)
        title = journal.bibjson().title
        alt = journal.bibjson().alternative_title
        titles = []
        if title is not None and title != "":
            titles.append(_normalise_title(title))
        if alt is not None and alt != "":
            titles.append(_normalise_title(alt))
        for variants in terms:
            for v in variants:
                if v in titles or len([t for t in titles if v in t]) > 0:
                    row = [variants[-1]] + _extract_journal_row(journal)
                    application_rows.append(row)
                    break

    with open(out, "w", encoding="utf-8") as o:
        writer = csv.writer(o)
        writer.writerow([
            "Supplied Title",
            "Type",
            "ISSN(s)",
            "Date Created",
            "Last Updated",
            "Date Applied",
            "Status",
            "Most Recent Note",
            "Title Matched",
            "Alternative Title Matched",
            "Link"
        ])
        for row in application_rows:
            writer.writerow(row)
        for row in journal_rows:
            writer.writerow(row)


def _normalise_title(title):
    throwlist = string.punctuation + '\n\t'
    unpunctitle = "".join(c if c not in throwlist else " " for c in title).strip()
    try:
        asciiunpunctitle = unidecode(unpunctitle)
    except:
        asciiunpunctitle = unpunctitle
    while True:
        if "  " not in asciiunpunctitle:
            break
        asciiunpunctitle = asciiunpunctitle.replace("  ", " ")
    return asciiunpunctitle.lower()


def _extract_report_row(application):
    bj = application.bibjson()
    issns = bj.issns()
    title = bj.title
    alt = bj.alternative_title
    status = application.application_status
    created = application.created_date
    last_updated = application.last_updated
    date_applied = application.suggested_on
    notes = application.ordered_notes
    latest_note = ""
    if notes is not None and len(notes) > 1:
        latest_note = notes[0].get("note")

    return [
        "Application",
        ", ".join(issns),
        created,
        last_updated,
        date_applied,
        status,
        latest_note,
        title,
        alt,
        "https://doaj.org/admin/suggestion/" + application.id
    ]


def _extract_journal_row(journal):
    bj = journal.bibjson()
    issns = bj.issns()
    title = bj.title
    alt = bj.alternative_title
    created = journal.created_date
    last_updated = journal.last_updated
    status = "public" if journal.is_in_doaj() else "withdrawn"
    notes = journal.ordered_notes
    latest_note = ""
    if notes is not None and len(notes) > 1:
        latest_note = notes[0].get("note")

    return [
        "Journal",
        ", ".join(issns),
        created,
        last_updated,
        "",
        status,
        latest_note,
        title,
        alt,
        "https://doaj.org/admin/journal/" + journal.id
    ]


def _prep_search_terms(input):
    terms = []
    with open(input) as f:
        reader = csv.reader(f)
        for row in reader:
            variants = _make_variants(row[0])
            terms.append(variants)
    return terms


def _make_variants(original):
    split_rx = "and|&"
    joins = ["and", "&"]

    variants = []
    # tokenise around the SPLIT_RX
    bits = re.split(split_rx, original)
    expanded = [bits]

    while True:
        if len(expanded) == 0:
            break
        next = []
        for candidate in expanded:
            if len(candidate) > 1:
                for j in joins:
                    ccopy = deepcopy(candidate)
                    ccopy[0] = ccopy[0] + j + ccopy[1]
                    del ccopy[1]
                    next.append(ccopy)
            else:
                variants.append(_normalise_title(candidate[0]))
        expanded = next

    # stick the original one in at the end for reference
    variants.append(original)
    return tuple(variants)


if __name__ == "__main__":
    list_by_title(INPUT, OUT)