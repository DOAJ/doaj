from datetime import datetime

from doajtest.fixtures.v2.applications import ApplicationFixtureFactory
from doajtest.fixtures.v2.journals import JournalFixtureFactory
from doajtest.testdrive.factory import TestDrive
from flask import url_for
from portality import constants
from portality import models
from portality.autocheck.checkers.issn_active import ISSNChecker
from portality.autocheck.resources.issn_org import ISSNOrgData
from portality.bll import DOAJ
from portality.core import app


class Autocheck(TestDrive):

    def setup(self) -> dict:
        un = self.create_random_str()
        pw = self.create_random_str()
        acc = models.Account.make_account(un + "@example.com", un, "Admin " + un, [constants.ROLE_ADMIN])
        acc.set_password(pw)
        acc.save()

        ##################################################
        ## Setup and Application with the following features
        ##
        ## - Print ISSN registered at ISSN.org
        ## - Electronic ISSN not registered at ISSN.org
        ## - 3 preservation services:
        ##    - CLOCKSS - currently archived
        ##    - LOCKSS - not currently archived
        ##    - PMC - not registered
        source = ApplicationFixtureFactory.make_application_source()
        ap = models.Application(**source)
        ap.application_type = constants.APPLICATION_TYPE_NEW_APPLICATION
        ap.remove_current_journal()
        ap.remove_related_journal()
        apbj = ap.bibjson()
        apbj.set_preservation(["CLOCKSS", "LOCKSS", "PMC", "PKP PN", "None"], "http://policy.example.com")
        ap.set_id(ap.makeid())

        # # data for autocheck no_none_value
        apbj.deposit_policy = ['None']
        apbj.persistent_identifier_scheme = ['None']

        ap.save()

        bj = ap.bibjson()
        pissn = bj.get_one_identifier(bj.P_ISSN)
        eissn = bj.get_one_identifier(bj.E_ISSN)

        thisyear = datetime.utcnow().year

        pissn_data = ISSNOrgData({
            "mainEntityOfPage": {
                "version": "Register"  # this means the ISSN is registered at ISSN.org
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
                    "temporalCoverage": "2019/2020"
                }
            ]
        })

        eissn_data = ISSNOrgData({
            "mainEntityOfPage": {
                "version": "Pending"  # this means the ISSN is not registered at ISSN.org
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
                    "temporalCoverage": "2019/2020"
                }
            ]
        })

        old_retrieve_from_source = ISSNChecker.retrieve_from_source
        ISSNChecker.retrieve_from_source = lambda *args, **kwargs: (
            eissn,
            "https://portal.issn.org/resource/ISSN/2682-4396",
            eissn_data,
            False,
            pissn,
            "https://portal.issn.org/resource/ISSN/2682-4396",
            pissn_data,
            False)

        acSvc = DOAJ.autochecksService()
        ac1 = acSvc.autocheck_application(ap)

        ##################################################
        ## Setup a Journal with the following features
        ##
        ## - Print ISSN registered at ISSN.org
        ## - Electronic ISSN not found
        ## - 3 preservation services:
        ##    - CLOCKSS - currently archived
        ##    - LOCKSS - not currently archived
        ##    - PMC - not registered

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
            "https://portal.issn.org/resource/ISSN/9999-000X",
            None,  # Don't pass in any data, so we get the Not Found response
            False,
            pissn,
            "https://portal.issn.org/resource/ISSN/2682-4396",
            pissn_data,
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

    def teardown(self, params):
        models.Account.remove_by_id(params["account"]["username"])
        models.Application.remove_by_id(params["application"]["id"])
        models.Journal.remove_by_id(params["journal"]["id"])
        models.Autocheck.remove_by_id(params["autocheck"]["application"])
        models.Autocheck.remove_by_id(params["autocheck"]["journal"])
        return {"status": "success"}
