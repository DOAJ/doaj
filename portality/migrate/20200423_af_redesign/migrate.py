"""
Migrate the DOAJ to index-per-type; migrating application and journal types, copies others directly.
Adds 'type' to every record, which is the model __type__ (necessary for index-per-type)

Source index (sconn) MUST be index-per-project, based on config from settings.py (or overrides):
    ELASTIC_SEARCH_HOST
    ELASTIC_SEARCH_DB

Target index (tconn) supports the app being configured to use a fresh index-per-type connection:
    ELASTIC_SEARCH_HOST
    ELASTIC_SEARCH_INDEX_PER_TYPE = True
    ELASTIC_SEARCH_DB_PREFIX
But an index-per-project connection above as will work too.
"""

from portality.core import app, es_connection, initialise_index
from portality.util import ipt_prefix

from portality.models.v1.suggestion import Suggestion as SuggestionV1
from portality.models.v1.journal import JournalBibJSON as JournalBibJSONV1
from portality.models.v2.application import Application as ApplicationV2
from portality.models.v2.journal import JournalLikeBibJSON as JournalLikeBibJSONV2

from portality.models.v1.journal import Journal as JournalV1
from portality.models.v2.journal import Journal as JournalV2

import esprit
from datetime import datetime, timedelta

CC_URLS = {
    "CC BY": "https://creativecommons.org/licenses/by/4.0/",
    "CC BY-NC": "https://creativecommons.org/licenses/by-nc/4.0/",
    "CC BY-NC-ND": "https://creativecommons.org/licenses/by-nc-nd/4.0/",
    "CC BY-NC-SA": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
    "CC BY-ND": "https://creativecommons.org/licenses/by-nd/4.0/",
    "CC BY-SA": "https://creativecommons.org/licenses/by-sa/4.0/"
}

permissive_bibjson_struct = {
    "fields": {
        "alternative_title": {"coerce": "unicode"},
        "boai": {"coerce": "bool"},
        "eissn": {"coerce": "unicode"},
        "pissn": {"coerce": "unicode"},
        "discontinued_date": {"coerce": "bigenddate"},
        "publication_time_weeks": {"coerce": "integer"},
        "title": {"coerce": "unicode"}
    },
    "lists": {
        "is_replaced_by": {"coerce": "issn", "contains": "field"},
        "keywords": {"contains": "field", "coerce": "unicode_lower"},
        "language": {"contains": "field", "coerce": "unicode"},
        "license": {"contains": "object"},
        "replaces": {"contains": "field", "coerce": "issn"},
        "subject": {"contains": "object"}
    },
    "objects": [
        "apc",
        "article",
        "copyright",
        "deposit_policy",
        "editorial",
        "institution",
        "other_charges",
        "pid_scheme",
        "plagiarism",
        "preservation",
        "publisher",
        "ref",
        "waiver"
    ],
    "structs": {
        "apc": {
            "fields": {
                "has_apc": {"coerce": "bool"},
                "url": {"coerce": "url", "set__allow_coerce_failure": True}
            },
            "lists": {
                "max": {"contains": "object"}
            },
            "structs": {
                "max": {
                    "fields": {
                        "currency": {"coerce": "currency_code"},
                        "price": {"coerce": "integer"}
                    }
                }
            }
        },
        "article": {
            "fields": {
                "license_display_example_url": {"coerce": "url", "set__allow_coerce_failure": True},
                "orcid": {"coerce": "bool"},
                "i4oc_open_citations": {"coerce": "bool"}
            },
            "lists": {
                "license_display": {"contains": "field", "coerce": "unicode",
                                    "allowed_values": ["embed", "display", "no"]},
            }
        },
        "copyright": {
            "fields": {
                "author_retains": {"coerce": "bool"},
                "url": {"coerce": "url", "set__allow_coerce_failure": True}
            }
        },
        "deposit_policy": {
            "fields": {
                "has_policy": {"coerce": "bool"},
                "is_registered": {"coerce": "bool"},
                "url": {"coerce": "url", "set__allow_coerce_failure": True}
            },
            "lists": {
                "service": {"contains": "field", "coerce": "unicode"}
            }
        },
        "editorial": {
            "fields": {
                "review_url": {"coerce": "url", "set__allow_coerce_failure": True},
                "board_url": {"coerce": "url", "set__allow_coerce_failure": True}
            },
            "lists": {
                "review_process": {"contains": "field", "coerce": "unicode"}
            }
        },
        "institution": {
            "fields": {
                "name": {"coerce": "unicode"},
                "country": {"coerce": "country_code"}
            }
        },
        "license": {
            "fields": {
                "type": {"coerce": "unicode"},
                "BY": {"coerce": "bool"},
                "NC": {"coerce": "bool"},
                "ND": {"coerce": "bool"},
                "SA": {"coerce": "bool"},
                "url": {"coerce": "url", "set__allow_coerce_failure": True}
            }
        },
        "other_charges": {
            "fields": {
                "has_other_charges": {"coerce": "bool"},
                "url": {"coerce": "url", "set__allow_coerce_failure": True}
            }
        },
        "pid_scheme": {
            "fields": {
                "has_pid_scheme": {"coerce": "bool"},
            },
            "lists": {
                "scheme": {"coerce": "unicode", "contains": "field"}
            }
        },
        "plagiarism": {
            "fields": {
                "detection": {"coerce": "bool"},
                "url": {"coerce": "url", "set__allow_coerce_failure": True}
            }
        },
        "preservation": {
            "fields": {
                "has_preservation": {"coerce": "unicode"},
                "url": {"coerce": "unicode", "set__allow_coerce_failure": True}
            },
            "lists": {
                "national_library": {"contains": "field", "coerce": "unicode"},
                "service": {"coerce": "unicode", "contains": "field"},
            },
            "structs": {
                "policy": {
                    "fields": {
                        "name": {"coerce": "unicode"},
                        "domain": {"coerce": "unicode"}
                    }
                }
            }
        },
        "publisher": {
            "fields": {
                "name": {"coerce": "unicode"},
                "country": {"coerce": "unicode"}
            }
        },
        "ref": {
            "fields": {
                "oa_statement": {"coerce": "url", "set__allow_coerce_failure": True},
                "journal": {"coerce": "url", "set__allow_coerce_failure": True},
                "aims_scope": {"coerce": "url", "set__allow_coerce_failure": True},
                "author_instructions": {"coerce": "url", "set__allow_coerce_failure": True},
                "license_terms": {"coerce": "url", "set__allow_coerce_failure": True},
            }
        },
        "subject": {
            "fields": {
                "code": {"coerce": "unicode"},
                "scheme": {"coerce": "unicode"},
                "term": {"coerce": "unicode"}
            }
        },
        "waiver": {
            "fields": {
                "has_waiver": {"coerce": "bool"},
                "url": {"coerce": "url", "set__allow_coerce_failure": True}
            }
        }
    }
}


def permissive_bibjson(self):
    bj = self.__seamless__.get_single("bibjson")
    if bj is None:
        self.__seamless__.set_single("bibjson", {})
        bj = self.__seamless__.get_single("bibjson")
    return JournalLikeBibJSONV2(bj, struct=permissive_bibjson_struct)


ApplicationV2.bibjson = permissive_bibjson
JournalV2.bibjson = permissive_bibjson


def application_migration(source, target):
    assert isinstance(source, SuggestionV1)
    assert isinstance(target, ApplicationV2)

    # all the bits that it has in common with all other journals
    journal_like_migration(source, target)

    # application status
    if source.application_status:
        target.set_application_status(source.application_status)

    # current journal
    if source.current_journal is not None:
        target.set_current_journal(source.current_journal)

    # related journal
    if source.related_journal is not None:
        target.set_related_journal(source.related_journal)

    # suggested date
    if source.suggested_on is not None:
        target.date_applied = source.suggested_on


def journal_migration(source, target):
    journal_like_migration(source, target)

    # current application
    if source.current_application is not None:
        target.set_current_application(source.current_application)

    # in DOAJ
    target.set_in_doaj(source.is_in_doaj())

    # related applications
    for ra in source.related_applications:
        target.add_related_application(ra.get("application_id"), ra.get("date_accepted"), ra.get("status"))

    # tick
    target.set_ticked(source.is_ticked())


def journal_like_migration(source, target):
    bibjson_migration(source, target)

    # id
    target.set_id(source.id)

    # bulk upload
    if source.bulk_upload_id:
        target.set_bulk_upload_id(source.bulk_upload_id)

    if source.contacts() and len(source.contacts()) > 0:
        target.set_contact(**source.contacts()[0])

    # editor
    if source.editor:
        target.set_editor(source.editor)

    # editor group
    if source.editor_group:
        target.set_editor_group(source.editor_group)

    # notes
    for note in source.notes:
        target.add_note(note.get("note"), note.get("date"))

    # owner
    if source.owner is not None:
        target.set_owner(source.owner)

    # seal
    target.set_seal(source.has_seal())

    # created date
    target.set_created(source.created_date)

    # last manual update
    if source.last_manual_update is not None:
        target.set_last_manual_update(source.last_manual_update)

    # last updated
    target.set_last_updated(source.last_updated)


def bibjson_migration(source, target):
    sbj = source.bibjson()
    tbj = target.bibjson()

    assert isinstance(sbj, JournalBibJSONV1)
    assert isinstance(tbj, JournalLikeBibJSONV2)

    # alternative title
    if sbj.alternative_title:
        tbj.alternative_title = sbj.alternative_title

    # apc value
    apc_avg = sbj.apc.get("average_price")
    apc_curr = sbj.apc.get("currency")
    if apc_avg is not None and apc_curr is not None:
        tbj.add_apc(apc_curr, apc_avg)
    else:
        tbj.has_apc = False

    # apc url
    if sbj.apc_url:
        tbj.apc_url = sbj.apc_url

    # archiving policies -> preservation
    policies = sbj.archiving_policy.get("policy", [])
    policy_url = sbj.archiving_policy.get("url")
    known = []
    nat_lib = None
    for p in policies:
        if isinstance(p, list):
            if p[0] == "A national library":
                nat_lib = p[1]
            else:
                known.append(p[1])
        else:
            known.append(p)
    if len(known) > 0 or policy_url is not None:
        if policy_url == "":
            policy_url = None
        tbj.set_preservation(known, policy_url)
    if nat_lib is not None:
        tbj.add_preservation_library(nat_lib)

    # author copyright
    retains = sbj.author_copyright.get("copyright", False)
    retains = True if retains == "True" else False if retains == "False" else retains
    if "url" in sbj.author_copyright and sbj.author_copyright.get("url") != "":
        tbj.copyright_url = sbj.author_copyright.get("url")
    tbj.author_retains_copyright = retains

    # publisher country
    if sbj.country:
        tbj.publisher_country = sbj.country

    # deposit policy
    if sbj.deposit_policy:
        tbj.deposit_policy = sbj.deposit_policy
    else:
        tbj.has_deposit_policy = False

    # discontinued date
    if sbj.discontinued_date:
        tbj.discontinued_date = sbj.discontinued_date

    # editorial review
    process = sbj.editorial_review.get("process")
    review_url = sbj.editorial_review.get("url")
    board_url = sbj.get_single_url("editorial_board")
    if review_url == "":
        review_url = None
    if board_url == "":
        board_url = None
    tbj.set_editorial_review(process, review_url, board_url)

    # pissn
    pissn = sbj.get_one_identifier(sbj.P_ISSN)
    if pissn is not None:
        tbj.pissn = pissn

    # eissn
    eissn = sbj.get_one_identifier(sbj.E_ISSN)
    if eissn is not None:
        tbj.eissn = eissn

    # institution
    if sbj.institution is not None:
        tbj.institution_name = sbj.institution

    # is replaced by
    if sbj.is_replaced_by is not None:
        tbj.is_replaced_by = sbj.is_replaced_by

    # keywords
    if sbj.keywords is not None:
        tbj.keywords = sbj.keywords

    # language
    if sbj.language is not None:
        tbj.set_language(sbj.language)

    # licence
    lic = sbj.get_license()
    if lic is not None:
        lurl = lic.get("url")
        by = lic.get("BY")
        nc = lic.get("NC")
        nd = lic.get("ND")
        sa = lic.get("SA")
        ltype = lic.get("type")

        typeurl = None
        if lurl is not None and lurl.startswith("https://creativecommons.org/"):
            typeurl = lurl
        if typeurl is None:
            typeurl = CC_URLS.get(lurl)

        tbj.add_license(ltype, typeurl, by=by, sa=sa, nc=nc, nd=nd)

        embedded = lic.get("embedded")
        tbj.article_license_display = ["embed"] if embedded else ["no"]

        example_url = lic.get("embedded_example_url")
        if example_url is not None and example_url != "":
            tbj.article_license_display_example_url = example_url

        open_access = lic.get("open_access", False)
        tbj.boai = open_access

        if typeurl != lurl and lurl is not None and lurl != "":
            tbj.license_terms_url = lurl

    # oa statement url
    oastatement_url = sbj.get_single_url("oa_statement")
    if oastatement_url is not None and oastatement_url != "":
        tbj.oa_statement_url = oastatement_url

    # homepage url
    homepage_url = sbj.get_single_url("homepage")
    if homepage_url is not None and homepage_url != "":
        tbj.journal_url = homepage_url

    # aims_scope_url
    aims_scope_url = sbj.get_single_url("aims_scope")
    if aims_scope_url is not None and aims_scope_url != "":
        tbj.aims_scope_url = aims_scope_url

    # author instructions
    author_instructions_url = sbj.get_single_url("author_instructions")
    if author_instructions_url is not None and author_instructions_url != "":
        tbj.author_instructions_url = author_instructions_url

    # waiver url
    waiver_url = sbj.get_single_url("waiver_policy")
    if waiver_url is not None and waiver_url != "":
        tbj.waiver_url = waiver_url
        tbj.has_waiver = True
    else:
        tbj.has_waiver = False

    # persistent identifier scheme
    if sbj.persistent_identifier_scheme is not None and len(sbj.persistent_identifier_scheme) > 0:
        tbj.pid_scheme = sbj.persistent_identifier_scheme
    else:
        tbj.has_pid_scheme = False

    # plagiarism detection
    has_detection = sbj.plagiarism_detection.get("detection", False)
    detection_url = sbj.plagiarism_detection.get("url")
    if detection_url == "":
        detection_url = None
    tbj.set_plagiarism_detection(detection_url, has_detection)

    # publication time
    if sbj.publication_time is not None:
        tbj.publication_time_weeks = sbj.publication_time

    # publisher name
    if sbj.publisher is not None:
        tbj.publisher_name = sbj.publisher

    # replaces
    if sbj.replaces is not None:
        tbj.replaces = sbj.replaces

    # subject classifications
    if sbj.subjects() is not None:
        tbj.subject = sbj.subjects()

    # submission/other charges
    if sbj.submission_charges_url is not None and sbj.submission_charges_url != "":
        tbj.other_charges_url = sbj.submission_charges_url
    if sbj.submission_charges.get("average_price") is not None:
        tbj.has_other_charges = True
    else:
        tbj.has_other_charges = False

    # title
    if sbj.title is not None:
        tbj.title = sbj.title


# Since we are running a migration, assume the source index has been initialised already, but the target may not have.
initialise_index(app, es_connection)

sconn = esprit.raw.Connection(app.config.get("ELASTIC_SEARCH_HOST"), app.config.get("ELASTIC_SEARCH_DB"))
tconn = es_connection
prefix = app.config.get("ELASTIC_SEARCH_DB_PREFIX")

migrate_types = [
    ("suggestion", "application", SuggestionV1, ApplicationV2, application_migration),
    ("journal", "journal", JournalV1, JournalV2, journal_migration)
]

copy_types = [
    "news",
    "editor_group",
    "lcc",
    "provenance",
    "harvester_state",
    "bulk_upload",  # I'm not sure we actually use this anywhere now
    "article",
    "lock",
    "account",
    "upload",
    "background_job",
    "cache"
]

batch_size = 1000

# which means we're dropping the following data
# * bulk_reapplication
# * article_history
# * journal_history
# * toc
# Start with the straight copy operations
for ct in copy_types:
    tt = ipt_prefix(ct)
    print("Copying", ct, "to", tt)
    batch = []
    total = 0
    first_page = esprit.raw.search(sconn, ct)
    max = first_page.json().get("hits", {}).get("total", 0)
    type_start = datetime.now()

    default_query = {
        "query": {"match_all": {}}
    }

    try:
        for result in esprit.tasks.scroll(sconn, ct, q=default_query, keepalive="1m", page_size=1000, scan=True):
            result['es_type'] = ct
            batch.append(result)
            if len(batch) >= batch_size:
                total += len(batch)
                print(datetime.now(), "writing ", len(batch), "to", tt, ";", total, "of", max)
                esprit.raw.bulk(tconn, batch, idkey="id", type_=tt, bulk_type="create")
                batch = []
                # do some timing predictions
                batch_tick = datetime.now()
                time_so_far = batch_tick - type_start
                seconds_so_far = time_so_far.total_seconds()
                estimated_seconds_remaining = ((seconds_so_far * max) / total) - seconds_so_far
                estimated_finish = batch_tick + timedelta(seconds=estimated_seconds_remaining)
                print('Estimated finish time for this type {0}.'.format(estimated_finish))

    except esprit.tasks.ScrollTimeoutException:
        # Try to write the part-batch to index
        if len(batch) > 0:
            total += len(batch)
            print(datetime.now(), "scroll timed out / writing ", len(batch), "to", tt, ";", total,
                  "of", max)
            esprit.raw.bulk(tconn, batch, idkey="id", type_=tt, bulk_type="create")
            batch = []
        else:
            print("Scroll timed out, and nothing to finalise")

    # Write the last part-batch to index
    if len(batch) > 0:
        total += len(batch)
        print(datetime.now(), "final result set / writing ", len(batch), "to", tt, ";", total,
              "of", max)
        esprit.raw.bulk(tconn, batch, idkey="id", type_=tt, bulk_type="create")

# now do the hard migrations
for smt, tmt, source_model, target_model, processor in migrate_types:
    tt = ipt_prefix(tmt)
    print("Migrating", smt, "to", tt)
    batch = []
    total = 0
    first_page = esprit.raw.search(sconn, smt)
    max = first_page.json().get("hits", {}).get("total", 0)
    type_start = datetime.now()

    default_query = {
        "query": {"match_all": {}}
    }

    try:
        for result in esprit.tasks.scroll(sconn, smt, q=default_query, keepalive="2m", page_size=1000, scan=True):
            source = source_model(**result)
            try:
                source.snapshot()  # FIXME: is this what we should actually do?  It means that the history system has a copy of the record at final stage, which seems sensible
            except AttributeError:
                # this type doesn't support snapshotting
                pass

            target = target_model()
            processor(source, target)
            target.prep(is_update=False)  # in order to regenerate all the index fields, etc
            target.data['es_type'] = tmt
            batch.append(target.data)
            if len(batch) >= batch_size:
                total += len(batch)
                print(datetime.now(), "writing ", len(batch), "to", tt, ";", total, "of", max)
                esprit.raw.bulk(tconn, batch, idkey="id", type_=tt, bulk_type="create")
                batch = []
                # do some timing predictions
                batch_tick = datetime.now()
                time_so_far = batch_tick - type_start
                seconds_so_far = time_so_far.total_seconds()
                estimated_seconds_remaining = ((seconds_so_far * max) / total) - seconds_so_far
                estimated_finish = batch_tick + timedelta(seconds=estimated_seconds_remaining)
                print('Estimated finish time for this type {0}.'.format(estimated_finish))

    except esprit.tasks.ScrollTimeoutException:
        # Try to write the part-batch to index
        if len(batch) > 0:
            total += len(batch)
            print(datetime.now(), "scroll timed out / writing ", len(batch), "to", tt, ";", total,
                  "of", max)
            esprit.raw.bulk(tconn, batch, idkey="id", type_=tt, bulk_type="create")
            batch = []
        else:
            print("Scroll timed out, no more to write")

    # Write the last part-batch to index
    if len(batch) > 0:
        total += len(batch)
        print(datetime.now(), "final result set / writing ", len(batch), "to", tt, ";", total, "of", max)
        esprit.raw.bulk(tconn, batch, idkey="id", type_=tt, bulk_type="create")
