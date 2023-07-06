from portality import constants
from doajtest.testdrive.factory import TestDrive
from doajtest.fixtures.v2.applications import ApplicationFixtureFactory
from doajtest.fixtures.v2.journals import JournalFixtureFactory
from portality import models
from datetime import datetime
from portality.autocheck.checkers.issn_active import ISSNActive, ISSNChecker
from portality.autocheck.resources.issn_org import ISSNOrgData
from portality.autocheck.checkers.keepers_registry import KeepersRegistry
from portality.bll import DOAJ
from flask import url_for
from portality.core import app

class Autocheck(TestDrive):

    def setup(self) -> dict:
        un = self.create_random_str()
        pw = self.create_random_str()
        acc = models.Account.make_account(un + "@example.com", un, "Admin " + un, [constants.ROLE_ADMIN])
        acc.set_password(pw)
        acc.save()

        source = ApplicationFixtureFactory.make_application_source()
        ap = models.Application(**source)
        ap.remove_current_journal()
        ap.remove_related_journal()
        ap.set_id(ap.makeid())
        ap.save()

        bj = ap.bibjson()
        pissn = bj.get_one_identifier(bj.P_ISSN)
        eissn = bj.get_one_identifier(bj.E_ISSN)

        thisyear = datetime.utcnow().year

        issn_data = ISSNOrgData({
            "mainEntityOfPage": {
                "version": "Register"
            },
            "subjectOf": [
                {
                    "@type": "ArchiveComponent",
                    "holdingArchive": {
                        "@id": "http://issn.org/organization/keepers#clockss"
                    },
                    "temporalCoverage": "2022/" + str(thisyear)
                },
                {
                    "@type": "ArchiveComponent",
                    "holdingArchive": {
                        "@id": "http://issn.org/organization/keepers#lockss"
                    },
                    "temporalCoverage": "2022/" + str(thisyear)
                }
            ]
        })

        old_retrieve_from_source = ISSNChecker.retrieve_from_source
        ISSNChecker.retrieve_from_source = lambda *args, **kwargs: (
            eissn,
            "https://portal.issn.org/resource/ISSN/2682-4396",
            issn_data,
            False,
            pissn,
            "https://portal.issn.org/resource/ISSN/2682-4396",
            issn_data,
            False)

        acSvc = DOAJ.autochecksService(
            autocheck_plugins=[
                # (journal, application, plugin)
                (True, True, ISSNActive),
                (True, True, KeepersRegistry)
            ]
        )
        ac1 = acSvc.autocheck_application(ap)

        source = JournalFixtureFactory.make_journal_source()
        j = models.Journal(**source)
        j.remove_current_application()
        j.set_id(ap.makeid())
        j.save()

        bj = j.bibjson()
        pissn = bj.get_one_identifier(bj.P_ISSN)
        eissn = bj.get_one_identifier(bj.E_ISSN)

        ISSNChecker.retrieve_from_source = lambda *args, **kwargs: (
            eissn,
            "https://portal.issn.org/resource/ISSN/2682-4396",
            issn_data,
            False,
            pissn,
            "https://portal.issn.org/resource/ISSN/2682-4396",
            issn_data,
            False)

        ac2 = acSvc.autocheck_journal(j)

        ISSNChecker.retrieve_from_source = old_retrieve_from_source

        return {
            "account": {
                "username": acc.id,
                "password": pw
            },
            "application": {
                "id": ap.id,
                "admin_url": app.config.get("BASE_URL") + url_for("admin.application", application_id=ap.id)
            },
            "journal": {
                "id": j.id,
                "admin_url": app.config.get("BASE_URL") + url_for("admin.journal_page", journal_id=j.id)
            },
            "autocheck": {
                "application": ac1.id,
                "journal": ac2.id
            }
        }

    def teardown(self, params) -> dict:
        models.Account.remove_by_id(params["account"]["username"])
        models.EditorGroup.remove_by_id(params["editor_group"]["id"])
        for nature, details in params["applications"].items():
            for detail in details:
                models.Application.remove_by_id(detail["id"])
        return {"status": "success"}
