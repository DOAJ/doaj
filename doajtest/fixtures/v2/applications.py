from copy import deepcopy
from datetime import datetime

import rstr

from portality import constants, regex
from doajtest.fixtures.v2.common import JOURNAL_LIKE_BIBJSON, EDITORIAL_FORM_EXPANDED, SUBJECT_FORM_EXPANDED, NOTES_FORM_EXPANDED, OWNER_FORM_EXPANDED, SEAL_FORM_EXPANDED
from doajtest.fixtures.v2.journals import JOURNAL_FORM_EXPANDED, JOURNAL_FORM
from portality.lib import dates
from portality.lib.dates import FMT_DATE_YM, FMT_YEAR
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
            template["bibjson"]["pissn"] = rstr.xeger(regex.ISSN_COMPILED)
            template["bibjson"]["eissn"] = rstr.xeger(regex.ISSN_COMPILED)
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
            form = deepcopy(JOURNAL_FORM)
            del form["pissn"]
            del form["eissn"]

        return form

    @staticmethod
    def make_application_form_info():
        return deepcopy(APPLICATION_FORM_EXPANDED)

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
                startts = dates.parse(h, FMT_DATE_YM)
                year, month = divmod(startts.month+1, 12)
                if month == 0:
                    month = 12
                    year = year - 1
                endts = datetime(startts.year + year, month, 1)
                start = dates.format(startts)
                end = dates.format(endts)
            elif period == "year":
                startts = dates.parse(h, FMT_YEAR)
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
        "application_type" : constants.APPLICATION_TYPE_UPDATE_REQUEST,
        "current_journal" : "poiuytrewq",
        "editor" : "associate",
        "editor_group" : "editorgroup",
        "notes" : [
            {"note" : "Second Note", "date" : "2014-05-22T00:00:00Z", "id" : "1234", 'author_id': 'fake_account_id__b'},
            {"note": "First Note", "date": "2014-05-21T14:02:45Z", "id" : "abcd", 'author_id': 'fake_account_id__a'},
        ],
        "owner" : "publisher",
        "related_journal" : "987654321123456789",
        "seal": False,
        "date_applied" : "2003-01-01T00:00:00Z"
    },
    "bibjson" : JOURNAL_LIKE_BIBJSON
}

_isbj = deepcopy(JOURNAL_LIKE_BIBJSON)
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
        "current_journal" : "1234567890"
    }
}

WORKFLOW_FORM_EXPANDED = {
    "application_status" : constants.APPLICATION_STATUS_PENDING
}

APPLICATION_FORM_EXPANDED = deepcopy(JOURNAL_FORM_EXPANDED)
APPLICATION_FORM_EXPANDED.update(deepcopy(NOTES_FORM_EXPANDED))
APPLICATION_FORM_EXPANDED.update(deepcopy(SUBJECT_FORM_EXPANDED))
APPLICATION_FORM_EXPANDED.update(deepcopy(OWNER_FORM_EXPANDED))
APPLICATION_FORM_EXPANDED.update(deepcopy(EDITORIAL_FORM_EXPANDED))
APPLICATION_FORM_EXPANDED.update(deepcopy(SEAL_FORM_EXPANDED))
APPLICATION_FORM_EXPANDED.update(deepcopy(WORKFLOW_FORM_EXPANDED))

from portality.crosswalks.application_form import ApplicationFormXWalk
APPLICATION_FORM = ApplicationFormXWalk.forminfo2multidict(APPLICATION_FORM_EXPANDED)
