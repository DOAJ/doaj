from flask import url_for

from doajtest.testdrive.factory import TestDrive
from doajtest.fixtures.article import ArticleFixtureFactory
from portality import constants
from portality import models
from portality.core import app

# The ISSNs used by the "with_references.xml" test resources for DOAJ, Crossref 4.4.2 and Crossref 5.3.1 XML
PISSN = "1111-1111"
EISSN = "2222-2222"

REFERENCES = [
    "Smith, J. (2020) A reference with a DOI. doi:10.1234/abc",
    "Jones, A. (2021) A reference with a URL. https://www.doaj.org/",
    "Brown, B. (2022) A reference with no identifier at all.",
    "Taylor, C. (2023) A reference with <i>markup</i> in it.",
]


class ArticleReferences(TestDrive):
    # ~~ArticleReferences:TestDrive -> ArticleReferences:Feature~~

    def setup(self) -> dict:
        # The XML test resources have fixed ISSNs, so make sure nothing else in the index holds them,
        # otherwise the uploads will not be attributed to the testdrive publisher
        self.eliminate_existing([PISSN, EISSN])

        publisher, ppw = self.publisher_account()
        admin, apw = self.admin_account()

        journal = self.journal_with_issns(publisher)

        # pre-seeded articles, so the display/API/OAI-PMH/RIS tests can be run without first uploading XML.
        # DOI and fulltext differ from the XML test resources, so uploading those still creates new articles
        with_refs = self.article(journal, f"Testdrive References {self.run_seed}", "10.1234/td-refs-" + self.run_seed,
                                 references=REFERENCES)
        no_refs = self.article(journal, f"Testdrive No References {self.run_seed}",
                               "10.1234/td-norefs-" + self.run_seed)

        base_url = app.config.get("BASE_URL")
        oai_identifier = "oai:doaj.org/article:" + with_refs.id

        return {
            "publisher": {
                "username": publisher.id,
                "password": ppw,
                "api_key": publisher.api_key
            },
            "admin": {
                "username": admin.id,
                "password": apw
            },
            "journal": {
                "id": journal.id,
                "pissn": PISSN,
                "eissn": EISSN,
                "toc": base_url + url_for("doaj.toc", identifier=EISSN)
            },
            "publisher_area": {
                "upload_xml": base_url + url_for("publisher.upload_file"),
                "metadata_form": base_url + url_for("publisher.metadata")
            },
            "article_with_references": {
                "id": with_refs.id,
                "title": with_refs.bibjson().title,
                "public_page": base_url + url_for("doaj.article_page", identifier=with_refs.id),
                "admin_edit": base_url + url_for("admin.article_page", article_id=with_refs.id),
                "api": base_url + url_for("api.retrieve_article", article_id=with_refs.id),
                "oai_doaj": base_url + url_for("oaipmh.oaipmh", specified="article", verb="GetRecord",
                                               metadataPrefix="oai_doaj", identifier=oai_identifier),
                "oai_dc": base_url + url_for("oaipmh.oaipmh", specified="article", verb="GetRecord",
                                             metadataPrefix="oai_dc", identifier=oai_identifier),
                "ris": base_url + url_for("doajservices.export_article_ris", article_id=with_refs.id, fmt="ris")
            },
            "article_without_references": {
                "id": no_refs.id,
                "title": no_refs.bibjson().title,
                "public_page": base_url + url_for("doaj.article_page", identifier=no_refs.id)
            },
            "non_renderable": {
                "accounts": [publisher.id, admin.id],
                "journals": [journal.id],
                "articles": [with_refs.id, no_refs.id]
            }
        }

    def teardown(self, params) -> dict:
        for acc_id in params["non_renderable"]["accounts"]:
            models.Account.remove_by_id(acc_id)
        for jid in params["non_renderable"]["journals"]:
            models.Journal.remove_by_id(jid)
        for aid in params["non_renderable"]["articles"]:
            models.Article.remove_by_id(aid)
        # make the removals visible before deleting by query, otherwise ES reports version conflicts
        models.Article.refresh()
        # also remove any articles created during testing, via the XML upload or the metadata form
        models.Article.delete_by_issns([PISSN, EISSN], snapshot=False)
        return self.SUCCESS

    @staticmethod
    def eliminate_existing(issns):
        for issn in issns:
            for j in models.Journal.find_by_issn(issn):
                j.delete()
        models.Article.delete_by_issns(issns, snapshot=False)

    def admin_account(self):
        un = self.create_random_str()
        pw = self.create_random_str()
        acc = models.Account.make_account(un + "@example.com", un, "Admin " + un, [constants.ROLE_ADMIN])
        acc.set_password(pw)
        acc.save()
        return acc, pw

    def journal_with_issns(self, owner):
        journal = self.journals_in_doaj(owner, n=1, save=False)[0]
        journal.bibjson().pissn = PISSN
        journal.bibjson().eissn = EISSN
        journal.save(blocking=True)
        return journal

    def article(self, journal, title, doi, references=None):
        source = ArticleFixtureFactory.make_article_source(eissn=EISSN, pissn=PISSN, with_id=False, in_doaj=True,
                                                           doi=doi,
                                                           fulltext="https://example.com/testdrive/" + doi)
        a = models.Article(**source)
        a.set_id(a.makeid())
        a.bibjson().title = title
        if references is not None:
            a.bibjson().set_references(references)
        a.save()
        return a
