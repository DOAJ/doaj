# -*- coding: UTF-8 -*-
from copy import deepcopy
from typing import Iterable
from portality import models

import rstr

from doajtest.fixtures.v2.common import EDITORIAL_FORM_EXPANDED, SUBJECT_FORM_EXPANDED, NOTES_FORM_EXPANDED, \
    OWNER_FORM_EXPANDED, JOURNAL_LIKE_BIBJSON, JOURNAL_LIKE_BIBJSON_FORM_EXPANDED
from portality.regex import ISSN_COMPILED
from portality.lib import dicts


class JournalFixtureFactory(object):
    @classmethod
    def save_journals(cls, journals, block=False, save_kwargs=None):
        if save_kwargs is None:
            save_kwargs = {}
        block_data = []
        for a in journals:
            a.save(**save_kwargs)
            block_data.append((a.id, a.last_updated))
        if block:
            models.Journal.blockall(block_data)

    @staticmethod
    def make_journal_source(in_doaj=False, overlay=None):
        template = deepcopy(JOURNAL_SOURCE)
        template['admin']['in_doaj'] = in_doaj
        if overlay is not None:
            template = dicts.deep_merge(template, overlay, overlay=True)
        return template

    @staticmethod
    def make_many_journal_sources(count=2, in_doaj=False) -> Iterable[dict]:
        journal_sources = []
        for i in range(0, count):
            template = deepcopy(JOURNAL_SOURCE)
            template['id'] = 'journalid{0}'.format(i)
            # now some very quick and very dirty date generation
            fakemonth = i
            if fakemonth < 1:
                fakemonth = 1
            if fakemonth > 9:
                fakemonth = 9
            template['created_date'] = "2000-0{fakemonth}-01T00:00:00Z".format(fakemonth=fakemonth)
            template["bibjson"]["pissn"] = rstr.xeger(ISSN_COMPILED)
            template["bibjson"]["eissn"] = rstr.xeger(ISSN_COMPILED)
            template['admin']['in_doaj'] = in_doaj
            template['bibjson']['title'] = 'Test Title {}'.format(i)
            journal_sources.append(deepcopy(template))
        return journal_sources

    @classmethod
    def make_n_journals(cls, n, in_doaj=True):
        sources = JournalFixtureFactory.make_many_journal_sources(count=n, in_doaj=in_doaj)
        journals = []
        for s in sources:
            journals.append(models.Journal(**s))
        return journals

    @staticmethod
    def make_journal_form():
        return deepcopy(JOURNAL_FORM)

    @staticmethod
    def make_journal_form_info():
        return deepcopy(JOURNAL_FORM_EXPANDED)

    @staticmethod
    def make_journal_with_data(**data):
        journal = deepcopy(JOURNAL_SOURCE)
        in_doaj = data['in_doaj'] if'in_doaj' in data else True
        journal['admin']['in_doaj'] = in_doaj
        if 'title' in data:
            journal["bibjson"]["title"] = data['title']
        if 'publisher_name' in data:
            journal["bibjson"]["publisher"]["name"] = data['publisher_name']
        if 'country' in data:
            journal["bibjson"]["publisher"]["country"] = data['country']
        if 'alternative_title' in data:
            journal["bibjson"]["alternative_title"] = data['alternative_title']
        return journal

    @staticmethod
    def make_bulk_edit_data():
        return deepcopy(JOURNAL_BULK_EDIT)

    @staticmethod
    def csv_headers():
        return deepcopy(CSV_HEADERS)

    @staticmethod
    def question_answers():
        return deepcopy(JOURNAL_QUESTION_ANSWERS)


JOURNAL_SOURCE = {
    "id": "abcdefghijk_journal",
    "created_date": "2000-01-01T00:00:00Z",
    "last_manual_update": "2001-01-01T00:00:00Z",
    "last_updated": "2002-01-01T00:00:00Z",
    "admin": {
        "current_application": "qwertyuiop",
        "editor_group": "editorgroup",
        "editor": "associate",
        "in_doaj": False,
        "notes": [
            {"note": "Second Note", "date": "2014-05-22T00:00:00Z", "id": "1234",
             "author_id": "fake_account_id__b"},
            {"note": "First Note", "date": "2014-05-21T14:02:45Z", "id": "abcd",
             "author_id": "fake_account_id__a"},
        ],
        "owner": "publisher",
        "related_applications": [
            {"application_id": "asdfghjkl", "date_accepted": "2018-01-01T00:00:00Z"},
            {"application_id": "zxcvbnm"}
        ],
        "ticked": True
    },
    "bibjson": JOURNAL_LIKE_BIBJSON
}

JOURNAL_FORM_EXPANDED = {}
JOURNAL_FORM_EXPANDED.update(JOURNAL_LIKE_BIBJSON_FORM_EXPANDED)
JOURNAL_FORM_EXPANDED.update(EDITORIAL_FORM_EXPANDED)
JOURNAL_FORM_EXPANDED.update(SUBJECT_FORM_EXPANDED)
JOURNAL_FORM_EXPANDED.update(NOTES_FORM_EXPANDED)
JOURNAL_FORM_EXPANDED.update(OWNER_FORM_EXPANDED)

from portality.crosswalks.journal_form import JournalFormXWalk

JOURNAL_FORM = JournalFormXWalk.forminfo2multidict(JOURNAL_FORM_EXPANDED)

JOURNAL_BULK_EDIT = {
    "publisher": "Test Publisher",
    "country": "DZ",
    "platform": "HighWire",
    "contact_email": "richard@example.com",
    "owner": "testuser",
    "contact_name": "Test User"
}

CSV_HEADERS = [
    "Journal title",
    "Journal URL",
    "URL in DOAJ",  # (added outside journal2questions)
    "When did the journal start to publish all content using an open license?",
    "Alternative title",
    "Journal ISSN (print version)",
    "Journal EISSN (online version)",
    "Keywords",
    "Languages in which the journal accepts manuscripts",
    "Publisher",
    "Country of publisher",
    "Other organisation",
    "Country of other organisation",
    "Journal license",
    "License attributes",
    "URL for license terms",
    "Machine-readable CC licensing information embedded or displayed in articles",
    "Author holds copyright without restrictions",
    "Copyright information URL",
    "Review process",
    "Review process information URL",
    "Journal plagiarism screening policy",
    "URL for journal's aims & scope",
    "URL for the Editorial Board page",
    "URL for journal's instructions for authors",
    "Average number of weeks between article submission and publication",
    "APC",
    "APC information URL",
    "APC amount",
    "Journal waiver policy (for developing country authors etc)",
    "Waiver policy information URL",
    "Has other fees",
    "Other fees information URL",
    "Preservation Services",
    "Preservation Service: national library",
    "Preservation information URL",
    "Deposit policy directory",
    "URL for deposit policy",
    "Persistent article identifiers",
    "Does the journal comply to DOAJ's definition of open access?",
    "Continues",
    "Continued By",
    "LCC Codes",
    "Subscribe to Open",
    'Subjects',  # (added outside journal2questions)
    'Added on Date',  # (added outside journal2questions)
    'Last updated Date',  # (added outside journal2questions)
    # 'Tick: Accepted after March 2014', Removed 2020-12-11
    "Number of Article Records",  # (added outside journal2questions)
    "Most Recent Article Added"  # (added outside journal2questions)
]

JOURNAL_QUESTION_ANSWERS = [
    'The Title',
    'http://journal.url',
    '2012',
    'Alternative Title',
    '1234-5678',
    '9876-5432',
    'word, key',
    'English, French',
    'The Publisher',
    "United States",
    'Society Institution',
    "United States",
    "Publisher's own license",
    'Attribution, No Commercial Usage',
    'http://licence.url',
    'Yes',
    'Yes',
    'http://copyright.com',
    'Open peer review, some bloke checks it out',
    'http://review.process',
    'Yes',
    'http://aims.scope',
    'http://editorial.board',
    'http://author.instructions.com',
    '8',
    'Yes',
    'http://apc.com',
    "2 GBP",
    'Yes',
    'http://waiver.policy',
    'Yes',
    'http://other.charges',
    'LOCKSS, CLOCKSS, A safe place',
    'Trinity; Imperial',
    'http://digital.archiving.policy',
    'Open Policy Finder, Store it',
    "http://deposit.policy",
    'DOI, ARK, PURL, PIDMachine',
    'Yes',
    "1111-1111",
    "2222-2222",
    "HB1-3840|H|SF600-1100",
    "Yes"
]
