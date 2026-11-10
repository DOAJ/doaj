import uuid
import random
from copy import deepcopy

from portality import models, constants
from portality.lib import dicts
from portality.models import JournalLikeObject, Note


def generate_unique_issn(index_check=False):
    """ Generate a unique -and valid- ISSN that isn't already present, by checking the index """

    while True:
        digits = [random.randint(0, 9) for _ in range(7)]
        checksum = (11 - sum(v * w for v, w in zip(digits, range(8, 1, -1))) % 11) % 11
        s = ''.join(map(str, digits))
        issn = f"{s[:4]}-{s[4:]}{'X' if checksum == 10 else checksum}"

        # Look in the index to check whether this is unique.
        if index_check:
            if len(models.Journal.find_by_issn(issn)) == len(models.Application.find_by_issn(issn)) == 0:
                return issn
        else:
            return issn

def make_object(klazz, data_stack, loaders=None):
    source = make_data(data_stack)
    obj = klazz(**source)
    if loaders is not None:
        for k, v in loaders.items():
            # TODO: this should check if the referenced field is present before
            # applying the loader
            obj = v(obj)
    return obj

def make_data(stack):
    result = deepcopy(stack[0])
    for s in stack[1:]:
        overlay = deepcopy(s)
        result = dicts.deep_merge(result, overlay, overlay=True)
    expressed = express(result)
    return expressed

def express(template):
    """
    Recursively walk the given template and return a copy where any value that is a
    callable is replaced by the result of calling that callable. Handles nested
    dicts, lists, tuples and sets. The original template is not modified.
    """
    # If the template itself is a callable, call it and then express the result
    if callable(template):
        return express(template())

    # Dict: keep keys as-is and process values
    if isinstance(template, dict):
        return {k: express(v) for k, v in template.items()}

    # List: process each element
    if isinstance(template, list):
        return [express(v) for v in template]

    # Tuple: process and return a tuple
    if isinstance(template, tuple):
        return tuple(express(v) for v in template)

    # Set: process elements (order will not be preserved)
    if isinstance(template, set):
        return {express(v) for v in template}

    # Fallback: return a deepcopy to avoid mutating original mutable objects
    return deepcopy(template)

JOURNAL_LIKE_BIBJSON_BASE = {
    "alternative_title": "Alternative Title",
    "apc": {
        "max": [
            {"currency": "GBP", "price": 2}
        ],
        "url": "http://apc.com",
        "has_apc": True
    },
    "article": {
        "license_display": ["Embed"],
        "license_display_example_url": "http://licence.embedded"
    },
    "boai": True,
    "copyright": {
        "author_retains": True,
        "url": "http://copyright.com"
    },
    "deposit_policy": {
        "has_policy" : True,
        "service": ["Open Policy Finder", "Store it"],
        "url": "http://deposit.policy"
    },
    "editorial": {
        "review_process": ["Open peer review", "some bloke checks it out"],
        "review_url": "http://review.process",
        "board_url": "http://editorial.board"
    },
    "eissn": lambda: generate_unique_issn(index_check=False),
    "institution": {
        "name": "Society Institution",
        "country": "US"
    },
    "keywords": ["word", "key"],
    "labels": ["s2o", "mirror"],
    "language": ["EN", "FR"],
    "license": [
        {
            "type": "Publisher's own license",
            "BY": True,
            "NC": True,
            "ND": False,
            "SA": False,
            "url": "http://licence.url"
        }
    ],
    "oa_start": 2012,
    "other_charges": {
        "has_other_charges" : True,
        "url": "http://other.charges"
    },
    "pid_scheme": {
        "has_pid_scheme" : True,
        "scheme": ["DOI", "ARK", "PURL", "PIDMachine"],
    },
    "pissn": lambda: generate_unique_issn(index_check=False),
    "plagiarism": {
        "detection": True,
        "url": "http://plagiarism.screening"
    },
    "preservation": {
        "has_preservation" : True,
        "service": ["LOCKSS", "CLOCKSS", "A safe place"],
        "national_library": ["Trinity", "Imperial"],
        "url": "http://digital.archiving.policy"
    },
    "publication_time_weeks": 8,
    "publisher": {
        "name": "The Publisher",
        "country": "US"
    },
    "ref": {
        "oa_statement": "http://oa.statement",
        "journal": "http://journal.url",
        "aims_scope": "http://aims.scope",
        "author_instructions": "http://author.instructions.com",
        "license_terms": "http://licence.url"
    },
    "subject": [
        {"scheme": "LCC", "term": "Economic theory. Demography", "code": "HB1-3840"},
        {"scheme": "LCC", "term": "Social Sciences", "code": "H"},
        {"scheme": "LCC", "term": "Veterinary medicine", "code": "SF600-1100"}
    ],
    "title": "The Title",
    "waiver": {
        "has_waiver" : True,
        "url": "http://waiver.policy"
    }
}

JOURNAL_LIKE_BIBJSON_FULL_LEGACY_FIXTURE = {
    "discontinued_date": "2001-01-01",
    "eissn": "9876-5432",
    "is_replaced_by": ["2222-2222"],
    "pissn": "1234-5678",
    "replaces": ["1111-1111"],
}

JOURNAL_BASE = {
    "id": lambda: uuid.uuid4().hex,
    "created_date": "2000-01-01T00:00:00Z",
    "last_manual_update": "2001-01-01T00:00:00Z",
    "last_updated": "2002-01-01T00:00:00Z",
    "admin": {
        "in_doaj": True,
        "note_ids": [
            "1234",
            "abcd"
        ],
        "owner": "publisher",
        "ticked": True,
        "last_full_review": "2025-01-01",
        "date_applied": "2019-06-15T00:00:00Z",
        "last_withdrawn": "2020-03-10T00:00:00Z",
        "last_reinstated": "2020-06-20T00:00:00Z",
        "last_owner_transfer": "2021-02-11T00:00:00Z"
    },
    "bibjson": JOURNAL_LIKE_BIBJSON_BASE
}

JOURNAL_FULL_LEGACY_FIXTURE = {
    "id": "abcdefghijk_journal",
    "admin": {
        "current_application": "qwertyuiop",
        "editor_group": "editorgroup",
        "editor": "associate",
        "in_doaj": False,
        "related_applications": [
            {"application_id": "asdfghjkl", "date_accepted": "2018-01-01T00:00:00Z"},
            {"application_id": "zxcvbnm"}
        ],
    },
    "bibjson": JOURNAL_LIKE_BIBJSON_FULL_LEGACY_FIXTURE
}

NOTES_BASE = {
    "id": lambda: uuid.uuid4().hex,
    "note": "First Note",
    "created_date": "2014-05-21T14:02:45Z",
    "author_id": "fake_account_id__a"
}

APPLICATION_BASE = {
    "id" : lambda: uuid.uuid4().hex,
    "created_date" :  "2000-01-01T00:00:00Z",
    "last_manual_update" : "2001-01-01T00:00:00Z",
    "last_updated" : "2002-01-01T00:00:00Z",
    "admin": {
        "application_status" : constants.APPLICATION_STATUS_PENDING,
        "application_type" : constants.APPLICATION_TYPE_NEW_APPLICATION,
        "note_ids": [
            "1234",
            "abcd"
        ],
        "owner" : "publisher",
        "date_applied" : "2003-01-01T00:00:00Z",
    },
    "bibjson" : JOURNAL_LIKE_BIBJSON_BASE
}

APPLICATION_FULL_LEGACY_FIXTURE = {
    "id" : "abcdefghijk",
    "admin": {
        "application_type" : constants.APPLICATION_TYPE_UPDATE_REQUEST,
        "current_journal" : "poiuytrewq",
        "editor" : "associate",
        "editor_group" : "editorgroup",
        "related_journal" : "987654321123456789",
        "date_rejected" : "2004-01-01T00:00:00Z",
    },
    "bibjson" : JOURNAL_LIKE_BIBJSON_FULL_LEGACY_FIXTURE
}

def default_load_notes(journal_like:JournalLikeObject):
    nids = journal_like.note_ids

    notes = {}
    for i, nid in enumerate(nids):
        overlay = {"id": nid}
        if i < 1:
            overlay["note"] = "Second Note"
            overlay["created_date"] = "2014-05-22T00:00:00Z"
            overlay["author_id"] = "fake_account_id__b"
        notes[nid] = make_object(Note, [NOTES_BASE, overlay])
    journal_like._notes = notes
    journal_like._notes_loaded = True

    return journal_like

JOURNAL_OBJECT_BASE_LOADERS = {
    "admin.note_ids": lambda j: default_load_notes(j),
}