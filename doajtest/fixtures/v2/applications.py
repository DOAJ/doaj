from copy import deepcopy
from datetime import datetime

import rstr

from doajtest.fixtures.v2.shared_generators import make_data, APPLICATION_BASE, APPLICATION_FULL_LEGACY_FIXTURE, \
    make_object, JOURNAL_OBJECT_BASE_LOADERS
from portality import constants, regex
from doajtest.fixtures.v2.common import JOURNAL_LIKE_BIBJSON, EDITORIAL_FORM_EXPANDED, SUBJECT_FORM_EXPANDED, NOTES_FORM_EXPANDED, OWNER_FORM_EXPANDED
from doajtest.fixtures.v2.common import build_flags_form_expanded
from doajtest.fixtures.v2.journals import JOURNAL_FORM_EXPANDED, JOURNAL_FORM
from portality.lib import dates, dicts
from portality.lib.dates import FMT_DATE_YM, FMT_YEAR
from portality.models import JournalLikeBibJSON
from portality.models.v2.application import Application
from portality.crosswalks.application_form import ApplicationFormXWalk

class ApplicationFixtureFactory(object):
    @staticmethod
    def make_update_request_source(overlay=None):
        if overlay is None:
            overlay = {}
        if "admin" not in overlay:
            overlay["admin"] = {}
        if "current_journal" not in overlay["admin"]:
            overlay["admin"]["current_journal"] = '123456789987654321'
        result = make_data([APPLICATION_BASE, APPLICATION_FULL_LEGACY_FIXTURE, overlay])
        return result

    @staticmethod
    def make_application_source(overlay=None):
        if overlay is None:
            overlay = {}
        if "admin" not in overlay:
            overlay["admin"] = {}
        if "application_type" not in overlay["admin"]:
            overlay["admin"]["application_type"] = constants.APPLICATION_TYPE_NEW_APPLICATION

        result = make_data([APPLICATION_BASE, APPLICATION_FULL_LEGACY_FIXTURE, overlay])
        del result["admin"]["current_journal"]
        return result

    @staticmethod
    def make_legacy_application_object(overlay=None):
        if overlay is None:
            overlay = {}
        application = make_object(Application,
                              [APPLICATION_BASE, APPLICATION_FULL_LEGACY_FIXTURE, overlay],
                              loaders=JOURNAL_OBJECT_BASE_LOADERS)
        return application

    @staticmethod
    def make_application_object(data_stack=None, klazz=None, loaders=None):
        application = make_object(klazz or Application,
                              data_stack or [APPLICATION_BASE, APPLICATION_FULL_LEGACY_FIXTURE],
                              loaders=loaders or JOURNAL_OBJECT_BASE_LOADERS)
        return application

    @classmethod
    def make_multiple_applications_legacy(cls, count, data_stack=None, klazz=None, loaders=None, vary=None):
        def legacy_vary(n, j: Application):
            j.set_id("applicationid{0}".format(n))
            j.set_current_journal('123456789')
            # now some very quick and very dirty date generation
            fakemonth = n
            if fakemonth < 1:
                fakemonth = 1
            if fakemonth > 9:
                fakemonth = 9
            j.set_created("2000-0{fakemonth}-01T00:00:00Z".format(fakemonth=fakemonth))
            bj: JournalLikeBibJSON = j.bibjson()
            bj.pissn = rstr.xeger(regex.ISSN_COMPILED)
            bj.eissn = rstr.xeger(regex.ISSN_COMPILED)
            bj.title = 'Test Title {}'.format(i)

        if vary is None:
            vary = [legacy_vary]

        journals = []
        for i in range(count):
            journal = cls.make_application_object(data_stack=data_stack, klazz=klazz, loaders=loaders)
            for v in vary:
                v(i, journal)
            journals.append(journal)

        return journals

    @staticmethod
    def make_application_form(role="maned", flag=None, **flag_kwargs):
        form = deepcopy(APPLICATION_FORM_EXPANDED)
        if role == "assed" or role == "editor":
            del form["editor_group"]
            del form["s2o"]
        elif role == "publisher":
            form = deepcopy(JOURNAL_FORM)
            del form["pissn"]
            del form["eissn"]
            del form["s2o"]
        if flag:
            flags_update = build_flags_form_expanded(**flag_kwargs)
            form.update(deepcopy(flags_update))

        app_form = ApplicationFormXWalk.forminfo2multidict(form)

        return app_form

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
        "date_applied" : "2003-01-01T00:00:00Z",
        "date_rejected" : "2004-01-01T00:00:00Z",
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
APPLICATION_FORM_EXPANDED.update(deepcopy(WORKFLOW_FORM_EXPANDED))

APPLICATION_FORM = ApplicationFormXWalk.forminfo2multidict(APPLICATION_FORM_EXPANDED)
