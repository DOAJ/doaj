from copy import deepcopy
from datetime import datetime

import rstr

from portality import constants
from doajtest.fixtures.common import EDITORIAL, SUBJECT, NOTES, OWNER, SEAL
from doajtest.fixtures.v2.journals import JOURNAL_SOURCE, JOURNAL_INFO
from portality.formcontext import forms
from portality.lib import dates
from portality.models.v2.application import Application


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
            template["bibjson"]["pissn"] = rstr.xeger(forms.ISSN_REGEX)
            template["bibjson"]["eissn"] = rstr.xeger(forms.ISSN_REGEX)
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
                    s = Application()
                    s.set_created(dates.random_date(start, end))
                    s.bibjson().country = country
                    apps.append(s)

        return apps


APPLICATION_SOURCE = {
    "id" : "abcdefghijk",
    "created_date" :  "2000-01-01T00:00:00Z",
    "last_manual_update" : "2001-01-01T00:00:00Z",
    "last_updated" : "2002-01-01T00:00:00Z",
    "admin": {
        "application_status" : constants.APPLICATION_STATUS_PENDING,
        "bulk_upload": "bulk123456789",
        "contact" : [
            {
                "email" : "contact@email.com",
                "name" : "Contact Name"
            }
        ],
        "current_journal" : "poiuytrewq",
        "editor" : "associate",
        "editor_group" : "editorgroup",
        "notes" : [
            {"note" : "Second Note", "date" : "2014-05-22T00:00:00Z", "id" : "1234"},
            {"note": "First Note", "date": "2014-05-21T14:02:45Z", "id" : "abcd"}
        ],
        "owner" : "Owner",
        "related_journal" : "987654321123456789",
        "seal": True,
        "date_applied" : "2003-01-01T00:00:00Z",
        "applicant": {
            "name" : "Suggester",
            "email" : "suggester@email.com"
        }
    },
    "bibjson" : deepcopy(JOURNAL_SOURCE['bibjson'])
}

_isbj = deepcopy(JOURNAL_SOURCE['bibjson'])
_isbj["preservation"] = {
    "has_preservation": True,
    "national_library": "Trinity",
    "url": "http://digital.archiving.policy",
    "service" : ["LOCKSS", "CLOCKSS", "A safe place"]
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
    "admin" : {
        "contact" :
        {
            "email" : "contact@email.com",
            "name" : "Contact Name"
        },
        "current_journal" : "1234567890",
        "applicant" : {
            "name" : "Applicant",
            "email" : "applicant@email.com"
        }
    }
}

WORKFLOW = {
    "application_status" : constants.APPLICATION_STATUS_PENDING
}

APPLICATION_FORMINFO = deepcopy(JOURNAL_INFO)
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
