from copy import deepcopy
from datetime import datetime

import rstr

from portality import constants
from doajtest.fixtures.common import EDITORIAL, SUBJECT, NOTES, OWNER, SEAL
from doajtest.fixtures.journals import JOURNAL_SOURCE, JOURNAL_INFO
from portality.formcontext import forms
from portality.lib import dates
from portality.models import Suggestion


class ApplicationFixtureFactory(object):
    @staticmethod
    def make_update_request_source():
        template = deepcopy(APPLICATION_SOURCE)
        template["admin"]["current_journal"] = '123456789987654321'
        return template

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
            template["admin"]["current_journal"] = '123456789'
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
    "admin" : {
        "application_status" : constants.APPLICATION_STATUS_PENDING,
        "notes" : [
            {"note" : "Second Note", "date" : "2014-05-22T00:00:00Z"},
            {"note": "First Note", "date": "2014-05-21T14:02:45Z"}
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
        ],
        "current_journal" : "1234567890"
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
    "application_status" : constants.APPLICATION_STATUS_PENDING
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
