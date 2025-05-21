from io import StringIO

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
from portality.lib import dates

from doajtest.fixtures import ArticleFixtureFactory, JournalFixtureFactory, JournalCSVFixtureFactory, SludgePump, DataDumpFixtureFactory
from store import StoreFactory


class Premium(TestDrive):

    def setup(self) -> dict:
        # Create the 5 different types of users who will have different experiences of the premium subscription
        un = self.create_random_str()
        pw1 = self.create_random_str()
        basic = models.Account.make_account(un + "@example.com", un, "Basic " + un, [constants.ROLE_PUBLISHER])
        basic.set_password(pw1)
        basic.save()

        un = self.create_random_str()
        pw2 = self.create_random_str()
        free_pdd = models.Account.make_account(un + "@example.com", un, "Free PDD " + un, [constants.ROLE_PUBLISHER, constants.ROLE_PUBLIC_DATA_DUMP])
        free_pdd.set_password(pw2)
        free_pdd.save()

        un = self.create_random_str()
        pw3 = self.create_random_str()
        premium = models.Account.make_account(un + "@example.com", un, "Premium " + un, [constants.ROLE_PUBLISHER, constants.ROLE_PREMIUM])
        premium.set_password(pw3)
        premium.save()

        un = self.create_random_str()
        pw4 = self.create_random_str()
        oai_premium = models.Account.make_account(un + "@example.com", un, "OAI Premium " + un, [constants.ROLE_PUBLISHER, constants.ROLE_PREMIUM_OAI])
        oai_premium.set_password(pw4)
        oai_premium.save()

        un = self.create_random_str()
        pw5 = self.create_random_str()
        pdd_premium = models.Account.make_account(un + "@example.com", un, "PDD Premium " + un, [constants.ROLE_PUBLISHER, constants.ROLE_PREMIUM_PDD])
        pdd_premium.set_password(pw5)
        pdd_premium.save()

        un = self.create_random_str()
        pw6 = self.create_random_str()
        csv_premium = models.Account.make_account(un + "@example.com", un, "CSV Premium " + un, [constants.ROLE_PUBLISHER, constants.ROLE_PREMIUM_CSV])
        csv_premium.set_password(pw6)
        csv_premium.save()

        # Create the csv and pdd records that will be used by the premium users
        csvstore = StoreFactory.get(constants.STORE__SCOPE__JOURNAL_CSV)
        container = app.config.get("STORE_JOURNAL_CSV_CONTAINER")
        current_csv = JournalCSVFixtureFactory.make_journal_csv({"export_date": dates.now(), "filename": "premium.csv"})
        current_csv.save()
        csvstore.store(container, current_csv.filename, source_stream=StringIO("premium csv"))
        free_csv = JournalCSVFixtureFactory.make_journal_csv({"export_date": dates.before_now(86400 * 29), "filename": "free.csv"})
        free_csv.save()
        csvstore.store(container, free_csv.filename, source_stream=StringIO("free csv"))

        pddstore = StoreFactory.get(constants.STORE__SCOPE__PUBLIC_DATA_DUMP)
        container = app.config.get("STORE_PUBLIC_DATA_DUMP_CONTAINER")
        current_pdd = DataDumpFixtureFactory.make_data_dump({
            "dump_date": dates.now(),
            "article": {
                "filename": "article_premium.tar.gz"
            },
            "journal": {
                "filename": "journal_premium.tar.gz"
            }
        })
        current_pdd.save()
        pddstore.store(container, current_pdd.article_filename, source_stream=StringIO("premium article"))
        pddstore.store(container, current_pdd.journal_filename, source_stream=StringIO("premium journal"))

        free_pdd_rec = DataDumpFixtureFactory.make_data_dump({
            "dump_date": dates.before_now(86400 * 29),
            "article": {
                "filename": "article_free.tar.gz"
            },
            "journal": {
                "filename": "journal_free.tar.gz"
            }
        })
        free_pdd_rec.save()
        pddstore.store(container, free_pdd_rec.article_filename, source_stream=StringIO("free article"))
        pddstore.store(container, free_pdd_rec.journal_filename, source_stream=StringIO("free journal"))

        # create a journal and article which are new enough to be excluded by the free OAI feed
        jsource = JournalFixtureFactory.make_journal_source(in_doaj=True, overlay={"created_date": dates.format(dates.before_now(86400))})
        journal = models.Journal(**jsource)
        journal.set_id(journal.makeid())
        journal.save()

        asource = ArticleFixtureFactory.make_article_source(journal.id, overlay={"created_date": dates.format(dates.before_now(86400))})
        article = models.Article(**asource)
        article.set_id(article.makeid())
        article.save()

        return {
            "accounts": {
                "basic": {
                    "username": basic.id,
                    "password": pw1
                },
                "free_pdd": {
                    "username": free_pdd.id,
                    "password": pw2
                },
                "premium": {
                    "username": premium.id,
                    "password": pw3
                },
                "oai_premium": {
                    "username": oai_premium.id,
                    "password": pw4
                },
                "pdd_premium": {
                    "username": pdd_premium.id,
                    "password": pw5
                },
                "csv_premium": {
                    "username": csv_premium.id,
                    "password": pw6
                }
            },
            "pdd": {
                "premium": current_pdd.id,
                "free": free_pdd_rec.id
            },
            "csv": {
                "premium": current_csv.id,
                "free": free_csv.id
            },
            "recent": {
                "journal": journal.id,
                "article": article.id
            }
        }

    def teardown(self, params):
        models.Account.remove_by_id(params["accounts"]["basic"]["username"])
        models.Account.remove_by_id(params["accounts"]["free_pdd"]["username"])
        models.Account.remove_by_id(params["accounts"]["premium"]["username"])
        models.Account.remove_by_id(params["accounts"]["oai_premium"]["username"])
        models.Account.remove_by_id(params["accounts"]["pdd_premium"]["username"])
        models.Account.remove_by_id(params["accounts"]["csv_premium"]["username"])

        csvstore = StoreFactory.get(constants.STORE__SCOPE__JOURNAL_CSV)
        container = app.config.get("STORE_JOURNAL_CSV_CONTAINER")

        premium_csv = models.JournalCSV.pull(params["csv"]["premium"])
        csvstore.delete_file(container, premium_csv.filename)
        premium_csv.delete()

        free_csv = models.JournalCSV.pull(params["csv"]["free"])
        csvstore.delete_file(container, free_csv.filename)
        free_csv.delete()

        pddstore = StoreFactory.get(constants.STORE__SCOPE__PUBLIC_DATA_DUMP)
        container = app.config.get("STORE_PUBLIC_DATA_DUMP_CONTAINER")

        premium_pdd = models.DataDump.pull(params["pdd"]["premium"])
        pddstore.delete_file(container, premium_pdd.article_filename)
        pddstore.delete_file(container, premium_pdd.journal_filename)
        premium_pdd.delete()

        free_pdd = models.DataDump.pull(params["pdd"]["free"])
        pddstore.delete_file(container, free_pdd.article_filename)
        pddstore.delete_file(container, free_pdd.journal_filename)
        free_pdd.delete()

        models.Journal.remove_by_id(params["recent"]["journal"])
        models.Article.remove_by_id(params["recent"]["article"])

        return {"status": "success"}
