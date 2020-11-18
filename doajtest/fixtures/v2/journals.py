# -*- coding: UTF-8 -*-
from copy import deepcopy
import rstr

from doajtest.fixtures.v2.common import EDITORIAL_FORM_EXPANDED, SUBJECT_FORM_EXPANDED, NOTES_FORM_EXPANDED, \
    OWNER_FORM_EXPANDED, SEAL_FORM_EXPANDED, JOURNAL_LIKE_BIBJSON, JOURNAL_LIKE_BIBJSON_FORM_EXPANDED

from portality.forms.utils import expanded2compact
from portality.regex import ISSN_COMPILED

class JournalFixtureFactory(object):
    @staticmethod
    def make_journal_source(in_doaj=False):
        template = deepcopy(JOURNAL_SOURCE)
        template['admin']['in_doaj'] = in_doaj
        return template

    @staticmethod
    def make_many_journal_sources(count=2, in_doaj=False):
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

    @staticmethod
    def make_journal_form():
        return deepcopy(JOURNAL_FORM)

    @staticmethod
    def make_journal_form_info():
        return deepcopy(JOURNAL_FORM_EXPANDED)

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
        "bulk_upload": "bulk_1234567890",
        "current_application": "qwertyuiop",
        "editor_group": "editorgroup",
        "editor": "associate",
        "in_doaj": False,
        "notes" : [
            {"note" : "Second Note", "date" : "2014-05-22T00:00:00Z", "id" : "1234"},
            {"note": "First Note", "date": "2014-05-21T14:02:45Z", "id" : "abcd"}
        ],
        "owner": "publisher",
        "related_applications": [
            {"application_id": "asdfghjkl", "date_accepted": "2018-01-01T00:00:00Z"},
            {"application_id": "zxcvbnm"}
        ],
        "seal": False,
        "ticked": True
    },
    "bibjson": JOURNAL_LIKE_BIBJSON
}

JOURNAL_FORM_EXPANDED = {}
JOURNAL_FORM_EXPANDED.update(JOURNAL_LIKE_BIBJSON_FORM_EXPANDED)
JOURNAL_FORM_EXPANDED.update(EDITORIAL_FORM_EXPANDED)
JOURNAL_FORM_EXPANDED.update(SEAL_FORM_EXPANDED)
JOURNAL_FORM_EXPANDED.update(SUBJECT_FORM_EXPANDED)
JOURNAL_FORM_EXPANDED.update(NOTES_FORM_EXPANDED)
JOURNAL_FORM_EXPANDED.update(OWNER_FORM_EXPANDED)

from portality.crosswalks.journal_form import JournalFormXWalk
JOURNAL_FORM = JournalFormXWalk.forminfo2multidict(JOURNAL_FORM_EXPANDED)

JOURNAL_BULK_EDIT = {
    "publisher": "Test Publisher",
    "doaj_seal": True,
    "country": "DZ",
    "platform": "HighWire",
    "contact_email": "richard@example.com",
    "owner": "testuser",
    "contact_name": "Test User"
}

CSV_HEADERS = [
    "Journal title",
    "Journal URL",
    "Alternative title",
    "Journal ISSN (print version)",
    "Journal EISSN (online version)",
    "Publisher",
    "Country of publisher",
    "Society or institution",
    "Country of society or institution",
    "Continues",
    "Continued By",
    "APC",
    "APC information URL",
    "APC amount",
    "Has other submission charges",
    "Other submission charges information URL",
    "Journal waiver policy (for developing country authors etc)",
    "Waiver policy information URL",
    "Preservations Services",
    "Preservation Service: national library",
    "Preservation information URL",
    "Permanent article identifiers",
    "Keywords",
    "Full text language",
    "URL for the Editorial Board page",
    "Review process",
    "Review process information URL",
    "URL for journal's aims & scope",
    "URL for journal's instructions for authors",
    "Journal plagiarism screening policy",
    "Plagiarism information URL",
    "Average number of weeks between submission and publication",
    "URL for journal's Open Access statement",
    "Machine-readable CC licensing information embedded or displayed in articles",
    "URL to an example page with embedded licensing information",
    "Journal license",
    "License attributes",
    "URL for license terms",
    "Does this journal allow unrestricted reuse in compliance with BOAI?",
    "Deposit policy directory",
    "URL for deposit policy",
    "Author holds copyright without restrictions",
    "Copyright information URL",
    "Article metadata includes ORCIDs",
    "Journal complies with I4OC standards for open citations",
    "LCC Codes",
    'DOAJ Seal',
    'Tick: Accepted after March 2014',
    'Added on Date',
    'Subjects',
    "Number of Article Records",
    "Most Recent Article Added"
]

JOURNAL_QUESTION_ANSWERS = [
    'The Title',
    'http://journal.url',
    'Alternative Title',
    '1234-5678',
    '9876-5432',
    'The Publisher',
    "United States",
    'Society Institution',
    "United States",
    "1111-1111",
    "2222-2222",
    'Yes',
    'http://apc.com',
    "2 GBP",
    'Yes',
    'http://other.charges',
    'Yes',
    'http://waiver.policy',
    'LOCKSS, CLOCKSS, A safe place',
    'Trinity; Imperial',
    'http://digital.archiving.policy',
    'DOI, ARK, PURL, PIDMachine',
    'word, key',
    'English, French',
    'http://editorial.board',
    'Open peer review, some bloke checks it out',
    'http://review.process',
    'http://aims.scope',
    'http://author.instructions.com',
    'Yes',
    'http://plagiarism.screening',
    '8',
    'http://oa.statement',
    'Yes',
    'http://licence.embedded',
    "Publisher's own license",
    'Attribution, No Commercial Usage',
    'http://licence.url',
    'Yes',
    'Sherpa/Romeo, Store it',
    "http://deposit.policy",
    'Yes',
    'http://copyright.com',
    'Yes',
    'No',
    "HB1-3840|H"
]
