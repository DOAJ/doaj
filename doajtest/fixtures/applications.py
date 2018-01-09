from copy import deepcopy
from datetime import datetime
import rstr

from doajtest.fixtures.journals import JOURNAL_SOURCE, JOURNAL_INFO
from doajtest.fixtures.common import EDITORIAL, SUBJECT, NOTES, OWNER, SEAL
from portality.models import Suggestion
from portality.lib import dates
from portality.formcontext import forms

class ApplicationFixtureFactory(object):
    @staticmethod
    def make_application_source():
        return deepcopy(APPLICATION_SOURCE)
    
    @staticmethod
    def make_many_application_sources(count=2, in_doaj=False):
        application_sources = []
        for i in range(0, count):
            template = deepcopy(APPLICATION_SOURCE)
            template['id'] = 'applicationid{0}'.format(i)
            # now some very quick and very dirty date generation
            fakemonth = i
            if fakemonth < 1:
                fakemonth = 1
            if fakemonth > 9:
                fakemonth = 9
            template['created_date'] = "2000-0{fakemonth}-01T00:00:00Z".format(fakemonth=fakemonth)
            template["bibjson"]['identifier'] = [
                {"type": "pissn", "id": rstr.xeger(forms.ISSN_REGEX)},
                {"type": "eissn", "id": rstr.xeger(forms.ISSN_REGEX)},
            ]
            template['bibjson']['title'] = 'Test Title {}'.format(i)
            application_sources.append(deepcopy(template))
        return application_sources

    @staticmethod
    def make_application_form(role="maned"):
        form = deepcopy(APPLICATION_FORM)
        if role == "assed" or role == "editor":
            del form["editor_group"]
        elif role == "publisher":
            UPDATE_REQUEST_FORMINFO = deepcopy(JOURNAL_INFO)
            UPDATE_REQUEST_FORMINFO.update(deepcopy(SUGGESTION))

            form = deepcopy(UPDATE_REQUEST_FORMINFO)
            form["keywords"] = ",".join(form["keywords"])
            del form["pissn"]
            del form["eissn"]
            del form["contact_name"]
            del form["contact_email"]
            del form["confirm_contact_email"]

        return form

    @staticmethod
    def make_application_form_info():
        return deepcopy(APPLICATION_FORMINFO)

    @staticmethod
    def make_reapp_source():
        return deepcopy(REAPP1_SOURCE)

    @staticmethod
    def make_reapp_unicode_source():
        return deepcopy(REAPP2_UNICODE_SOURCE)

    @classmethod
    def incoming_application(cls):
        return deepcopy(INCOMING_SOURCE)

    @classmethod
    def make_application_spread(cls, desired_output, period):
        desired_output = deepcopy(desired_output)
        header = desired_output[0]
        del desired_output[0]
        del header[0]
        ranges = []
        for h in header:
            start = None
            end = None
            if period == "month":
                startts = dates.parse(h, "%Y-%m")
                year, month = divmod(startts.month+1, 12)
                if month == 0:
                    month = 12
                    year = year - 1
                endts = datetime(startts.year + year, month, 1)
                start = dates.format(startts)
                end = dates.format(endts)
            elif period == "year":
                startts = dates.parse(h, "%Y")
                endts = datetime(startts.year + 1, 1, 1)
                start = dates.format(startts)
                end = dates.format(endts)

            ranges.append((start, end))

        apps = []
        for row in desired_output:
            country = row[0]
            del row[0]
            for i in range(len(row)):
                count = row[i]
                start, end = ranges[i]
                for j in range(count):
                    s = Suggestion()
                    s.set_created(dates.random_date(start, end))
                    s.bibjson().country = country
                    apps.append(s)

        return apps

APPLICATION_SOURCE = {
    "id" : "abcdefghijk",
    "created_date" : "2000-01-01T00:00:00Z",
    "bibjson": deepcopy(JOURNAL_SOURCE['bibjson']),
    "suggestion" : {
        "suggester" : {
            "name" : "Suggester",
            "email" : "suggester@email.com"
        },
        "articles_last_year" : {
            "count" : 16,
            "url" : "http://articles.last.year"
        },
        "article_metadata" : True
    },
    "admin" : {
        "application_status" : "pending",
        "notes" : [
            {"note" : "First Note", "date" : "2014-05-21T14:02:45Z"},
            {"note" : "Second Note", "date" : "2014-05-22T00:00:00Z"}
        ],
        "contact" : [
            {
                "email" : "contact@email.com",
                "name" : "Contact Name"
            }
        ],
        "owner" : "Owner",
        "editor_group" : "editorgroup",
        "editor" : "associate",
        "seal" : True,
        "current_journal" : "123456789987654321",
        "related_journal" : "987654321123456789"
    }
}

_isbj = deepcopy(JOURNAL_SOURCE['bibjson'])
_isbj["archiving_policy"] = {
    "policy" : [
        {"name" : "LOCKSS"},
        {"name" : "CLOCKSS"},
        {"name" : "Trinity", "domain" : "A national library"},
        {"name" : "A safe place", "domain" : "Other"}
    ],
    "url": "http://digital.archiving.policy"
}
del _isbj["subject"]
del _isbj["replaces"]
del _isbj["is_replaced_by"]
del _isbj["discontinued_date"]

INCOMING_SOURCE = {
    "id" : "ignore_me",
    "created_date" : "2001-01-01T00:00:00Z",
    "last_updated" : "2001-01-01T00:00:00Z",

    "bibjson": _isbj,
    "suggestion" : {
        "articles_last_year" : {
            "count" : 16,
            "url" : "http://articles.last.year"
        },
        "article_metadata" : True
    },
    "admin" : {
        "contact" : [
            {
                "email" : "contact@email.com",
                "name" : "Contact Name"
            }
        ]
    }
}

SUGGESTION = {
    "articles_last_year" : 16,
    "articles_last_year_url" : "http://articles.last.year",
    "metadata_provision" : "True"
}

SUGGESTER = {
    "suggester_name" : "Suggester",
    "suggester_email" : "suggester@email.com",
    "suggester_email_confirm" : "suggester@email.com"
}

WORKFLOW = {
    "application_status" : "pending"
}

APPLICATION_FORMINFO = deepcopy(JOURNAL_INFO)
APPLICATION_FORMINFO.update(deepcopy(SUGGESTION))
APPLICATION_FORMINFO.update(deepcopy(SUGGESTER))
APPLICATION_FORMINFO.update(deepcopy(NOTES))
APPLICATION_FORMINFO.update(deepcopy(SUBJECT))
APPLICATION_FORMINFO.update(deepcopy(OWNER))
APPLICATION_FORMINFO.update(deepcopy(EDITORIAL))
APPLICATION_FORMINFO.update(deepcopy(SEAL))
APPLICATION_FORMINFO.update(deepcopy(WORKFLOW))

APPLICATION_FORM = deepcopy(APPLICATION_FORMINFO)
APPLICATION_FORM["keywords"] = ",".join(APPLICATION_FORM["keywords"])
notes = APPLICATION_FORM["notes"]
del APPLICATION_FORM["notes"]
i = 0
for n in notes:
    notekey = "notes-" + str(i) + "-note"
    datekey = "notes-" + str(i) + "-date"
    APPLICATION_FORM[notekey] = n.get("note")
    APPLICATION_FORM[datekey] = n.get("date")
    i += 1

REAPP1_SOURCE = {
    "index":{
        "oa_statement_url":"http://oa.statement",
        "publisher":[
            "The Publisher",
            "Society Institution"
        ],
        "schema_subject":[
            "LCC:Social Sciences",
            "LCC:Economic theory. Demography"
        ],
        "license":[
            "CC MY"
        ],
        "classification":[
            "Social Sciences",
            "Economic theory. Demography"
        ],
        "title":[
            "The Title"
        ],
        "country":"United States",
        "waiver_policy_url":"http://waiver.policy",
        "issn":[
            "1234-5678",
            "9876-5432"
        ],
        "language":[
            "FR",
            "EN"
        ],
        "homepage_url":"http://journal.url",
        "aims_scope_url":"http://aims.scope",
        "schema_code":[
            "LCC:HB1-3840",
            "LCC:H"
        ],
        "author_instructions_url":"http://author.instructions.com",
        "subject":[
            "word",
            "Social Sciences",
            "key",
            "Economic theory. Demography"
        ],
        "editorial_board_url":"http://editorial.board"
    },
    "last_updated":"2014-10-29T12:23:47Z",
    "admin":{
        "notes":[
            {
                "note":"First Note",
                "date":"2014-05-21T14:02:45Z"
            },
            {
                "note":"Second Note",
                "date":"2014-05-22T00:00:00Z"
            }
        ],
        "contact":[
            {
                "email":"contact@email.com",
                "name":"Contact Name"
            }
        ],
        "application_status":"update_request",
        "owner":"Owner",
        "editor_group":"editorgroup",
        "current_journal":"abcdefghijk_journal",
        "editor":"associate"
    },
    "suggestion":{
        "suggested_on":"2014-10-29T12:23:47Z"
    },
    "created_date":"2014-10-29T12:23:47Z",
    "id":"ba7c9b024ede4528bd65cd9b7a2dba20",
    "bibjson":{
        "replaces" : ["1111-1111"],
        "is_replaced_by" : ["2222-2222"],
        "discontinued_date" : "2001-01-01",
        "allows_fulltext_indexing":True,
        "submission_charges":{
            "currency":"USD",
            "average_price":4
        },
        "author_publishing_rights":{
            "url":"http://publishing.rights",
            "publishing_rights":"True"
        },
        "keywords":[
            "word",
            "key"
        ],
        "apc":{
            "currency":"GBP",
            "average_price":2
        },
        "subject":[
            {
                "scheme":"LCC",
                "term":"Economic theory. Demography",
                "code":"HB1-3840"
            },
            {
                "scheme":"LCC",
                "term":"Social Sciences",
                "code":"H"
            }
        ],
        "article_statistics":{
            "url":"http://download.stats",
            "statistics":True
        },
        "title":"The Title",
        "publication_time":8,
        "provider":"Platform Host Aggregator",
        "format":[
            "HTML",
            "XML",
            "Wordperfect"
        ],
        "archiving_policy":{
            "known":["LOCKSS", "CLOCKSS"],
            "nat_lib" : "Trinity",
            "other" : "A safe place",
            "url":"http://digital.archiving.policy"
        },
        "plagiarism_detection":{
            "detection":True,
            "url":"http://plagiarism.screening"
        },
        "link":[
            {
                "url":"http://journal.url",
                "type":"homepage"
            },
            {
                "url":"http://waiver.policy",
                "type":"waiver_policy"
            },
            {
                "url":"http://editorial.board",
                "type":"editorial_board"
            },
            {
                "url":"http://aims.scope",
                "type":"aims_scope"
            },
            {
                "url":"http://author.instructions.com",
                "type":"author_instructions"
            },
            {
                "url":"http://oa.statement",
                "type":"oa_statement"
            }
        ],
        "oa_start":{
            "year":1980
        },
        "editorial_review":{
            "process":"Open peer review",
            "url":"http://review.process"
        },
        "author_copyright":{
            "url":"http://copyright.com",
            "copyright":"True"
        },
        "institution":"Society Institution",
        "deposit_policy":[
            "Sherpa/Romeo",
            "Store it"
        ],
        "language":[
            "EN",
            "FR"
        ],
        "license":[
            {
                "open_access":True,
                "embedded":True,
                "title":"CC MY",
                "url":"http://licence.url",
                "NC":True,
                "ND":False,
                "embedded_example_url":"http://licence.embedded",
                "SA":False,
                "type":"CC MY",
                "BY":True
            }
        ],
        "alternative_title":"Alternative Title",
        "country":"US",
        "publisher":"The Publisher",
        "persistent_identifier_scheme":[
            "DOI",
            "ARK",
            "PURL"
        ],
        "identifier":[
            {
                "type":"pissn",
                "id":"1234-5678"
            },
            {
                "type":"eissn",
                "id":"9876-5432"
            }
        ]
    }
}

REAPP2_UNICODE_SOURCE = {
    u"index":{
        u"oa_statement_url":u"http://oa.statement",
        u"publisher":[
            u"The Publisher",
            u"Society Institution"
        ],
        u"schema_subject":[
            u"LCC:Social Sciences",
            u"LCC:Economic theory. Demography"
        ],
        u"license":[
            u"CC MY"
        ],
        u"classification":[
            u"Social Sciences",
            u"Economic theory. Demography"
        ],
        u"title":[
            u"The Title"
        ],
        u"country":u"United States",
        u"waiver_policy_url":u"http://waiver.policy",
        u"issn":[
            u"1234-5678",
            u"9876-5432"
        ],
        u"language":[
            u"FR",
            u"EN"
        ],
        u"homepage_url":u"http://journal.url",
        u"aims_scope_url":u"http://aims.scope",
        u"schema_code":[
            u"LCC:HB1-3840",
            u"LCC:H"
        ],
        u"author_instructions_url":u"http://author.instructions.com",
        u"subject":[
            u"word",
            u"Social Sciences",
            u"key",
            u"Economic theory. Demography"
        ],
        u"editorial_board_url":u"http://editorial.board"
    },
    u"last_updated":u"2014-10-29T12:23:47Z",
    u"admin":{
        u"notes":[
            {
                u"note":u"First Note",
                u"date":u"2014-05-21T14:02:45Z"
            },
            {
                u"note":u"Second Note",
                u"date":u"2014-05-22T00:00:00Z"
            }
        ],
        u"contact":[
            {
                u"email":u"contact@email.com",
                u"name":u"Contact Name"
            }
        ],
        u"application_status":u"update_request",
        u"owner":u"Owner",
        u"editor_group":u"editorgroup",
        u"current_journal":u"abcdefghijk_journal",
        u"editor":u"associate"
    },
    u"suggestion":{
        u"suggested_on":u"2014-10-29T12:23:47Z"
    },
    u"created_date":u"2014-10-29T12:23:47Z",
    u"id":u"ba7c9b024ede4528bd65cd9b7a2dba20",
    u"bibjson":{
        u"replaces" : [u"1111-1111"],
        u"is_replaced_by" : [u"2222-2222"],
        u"discontinued_date" : u"2001-01-01",
        u"allows_fulltext_indexing":True,
        u"submission_charges":{
            u"currency":u"USD",
            u"average_price":4
        },
        u"author_publishing_rights":{
            u"url":u"http://publishing.rights",
            u"publishing_rights":u"True"
        },
        u"keywords":[
            u"word",
            u"key"
        ],
        u"apc":{
            u"currency":u"GBP",
            u"average_price":2
        },
        u"subject":[
            {
                u"scheme":u"LCC",
                u"term":u"Economic theory. Demography",
                u"code":u"HB1-3840"
            },
            {
                u"scheme":u"LCC",
                u"term":u"Social Sciences",
                u"code":u"H"
            }
        ],
        u"article_statistics":{
            u"url":u"http://download.stats",
            u"statistics":True
        },
        u"title":u"The Title",
        u"publication_time":8,
        u"provider":u"Platform Host Aggregator",
        u"format":[
            u"HTML",
            u"XML",
            u"Wordperfect"
        ],
        u"archiving_policy":{
            u"known" : [u"LOCKSS", u"CLOCKSS"],
            u"other" : u"A safe place",
            u"nat_lib" : u"Trinity",
            u"url":u"http://digital.archiving.policy"
        },
        u"plagiarism_detection":{
            u"detection":True,
            u"url":u"http://plagiarism.screening"
        },
        u"link":[
            {
                u"url":u"http://journal.url",
                u"type":u"homepage"
            },
            {
                u"url":u"http://waiver.policy",
                u"type":u"waiver_policy"
            },
            {
                u"url":u"http://editorial.board",
                u"type":u"editorial_board"
            },
            {
                u"url":u"http://aims.scope",
                u"type":u"aims_scope"
            },
            {
                u"url":u"http://author.instructions.com",
                u"type":u"author_instructions"
            },
            {
                u"url":u"http://oa.statement",
                u"type":u"oa_statement"
            }
        ],
        u"oa_start":{
            u"year":1980
        },
        u"editorial_review":{
            u"process":u"Open peer review",
            u"url":u"http://review.process"
        },
        u"author_copyright":{
            u"url":u"http://copyright.com",
            u"copyright":u"True"
        },
        u"institution":u"Society Institution",
        u"deposit_policy":[
            u"Sherpa/Romeo",
            u"Store it"
        ],
        u"language":[
            u"EN",
            u"FR"
        ],
        u"license":[
            {
                u"open_access":True,
                u"embedded":True,
                u"title":u"CC MY",
                u"url":u"http://licence.url",
                u"NC":True,
                u"ND":False,
                u"embedded_example_url":u"http://licence.embedded",
                u"SA":False,
                u"type":u"CC MY",
                u"BY":True
            }
        ],
        u"alternative_title":u"Alternative Title",
        u"country":u"US",
        u"publisher":u"The Publisher",
        u"persistent_identifier_scheme":[
            u"DOI",
            u"ARK",
            u"PURL"
        ],
        u"identifier":[
            {
                u"type":u"pissn",
                u"id":u"1234-5678"
            },
            {
                u"type":u"eissn",
                u"id":u"9876-5432"
            }
        ]
    }
}
