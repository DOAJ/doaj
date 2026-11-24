import json

from flask import url_for

from doajtest.testdrive.factory import TestDrive
from portality import constants, models
from portality.core import app
from portality.models.article import ArticleQuery

ORCID = "https://orcid.org/0000-0001-2345-6789"

DOAJ_XML = """<?xml version="1.0" encoding="UTF-8"?>
<records>
    <record>
        <language>eng</language>
        <publisher>Testdrive Publisher</publisher>
        <journalTitle>Testdrive Journal</journalTitle>
        <issn>{pissn}</issn>
        <eissn>{eissn}</eissn>
        <publicationDate>2026</publicationDate>
        <documentType>article</documentType>
        <title language="eng">XML Multiple Affiliations {seed}</title>
        <authors>
            <author>
                <name>Jane Doe</name>
                <affiliationId>1</affiliationId>
                <affiliationId>2</affiliationId>
                <orcid_id>{orcid}</orcid_id>
            </author>
            <author>
                <name>John Smith</name>
                <affiliationId>2</affiliationId>
                <affiliationId>3</affiliationId>
            </author>
        </authors>
        <affiliationsList>
            <affiliationName affiliationId="1">University of Oxford</affiliationName>
            <affiliationName affiliationId="2">Harvard University</affiliationName>
            <affiliationName affiliationId="3">MIT</affiliationName>
        </affiliationsList>
        <fullTextUrl>https://example.com/xml-multiple-affiliations-{seed}</fullTextUrl>
    </record>
</records>"""

# The ISSNs used by the "with_references.xml" test resources for DOAJ, Crossref 4.4.2 and Crossref 5.3.1 XML
PISSN = "1111-1111"
EISSN = "2222-2222"

class MultipleAffiliations(TestDrive):
    OAI_ARTICLE_SET = "article"

    def setup(self) -> dict:
        # The XML test resources have fixed ISSNs, so make sure nothing else in the index holds them,
        # otherwise the uploads will not be attributed to the testdrive publisher
        self.eliminate_existing([PISSN, EISSN])

        publisher, publisher_pw = self.publisher_account()
        admin, admin_pw = self.admin_account()
        journal = self.journals_in_doaj(publisher, n=1, block=True)[0]
        journal.bibjson().pissn = PISSN
        journal.bibjson().eissn = EISSN
        journal.save(blocking=True)
        pissn, eissn = journal.bibjson().pissn, journal.bibjson().eissn

        # one article already in the index, so the article page can be checked without uploading
        article = self.articles(journal, n=1, save=False)[0]
        article.bibjson().author = [
            {"name": "Ana Author", "affiliations": ["University of Oxford", "Harvard University", "MIT"], "orcid_id": ORCID},
            {"name": "Ben Author", "affiliations": ["Sorbonne University"]},
            {"name": "Cat Author"},
        ]
        article.save(blocking=True)

        def api_body(title, author):
            return json.dumps({
                "bibjson": {
                    "title": f"{title} {self.run_seed}",
                    "identifier": [{"type": "eissn", "id": eissn}, {"type": "pissn", "id": pissn}],
                    "link": [{"type": "fulltext", "content_type": "HTML",
                              "url": f"https://example.com/{title.lower().replace(' ', '-')}-{self.run_seed}"}],
                    "author": [author],
                }
            })

        base = app.config.get("BASE_URL", "")
        report = {
            "accounts": {
                "publisher": {"username": publisher.id, "password": publisher_pw, "api_key": publisher.api_key},
                "admin": {"username": admin.id, "password": admin_pw},
            },
        }
        self.report_journal_ids([journal], report)
        self.report_article_ids([article], report)
        report["links"] = {
            "login": base + url_for("account.login"),
            "article_page": base + url_for("doaj.article_page", identifier=article.id),
            "journal_toc": base + url_for("doaj.toc", identifier=eissn),
            "publisher_xml_upload": base + url_for("publisher.upload_file"),
            "publisher_metadata_form": base + url_for("publisher.metadata"),
            "admin_article_edit": base + url_for("admin.article_page", article_id=article.id),
            "oai_doaj_record": base + url_for("oaipmh.oaipmh", specified=self.OAI_ARTICLE_SET, verb="GetRecord",
                                              metadataPrefix="oai_doaj",
                                              identifier=f"oai:doaj.org/article:{article.id}"),
            "api_create_article": base + url_for("api.create_article", api_key=publisher.api_key),
        }
        report["upload_data"] = {
            "journal_pissn": pissn,
            "journal_eissn": eissn,
            "doaj_xml": DOAJ_XML.format(pissn=pissn, eissn=eissn, seed=self.run_seed, orcid=ORCID),
            "api_json_affiliations_list": api_body(
                "API Multiple Affiliations", {"name": "Api Author", "affiliations": ["Uni One", "Uni Two"]}),
            "api_json_legacy_affiliation": api_body(
                "API Legacy Affiliation", {"name": "Legacy Author", "affiliation": "Old Style University"}),
        }
        return report

    def admin_account(self):
        un = self.create_random_str()
        pw = self.create_random_str()
        acc = models.Account.make_account(un + "@example.com", un, "Admin " + un, [constants.ROLE_ADMIN])
        acc.set_password(pw)
        acc.save(blocking=True)
        return acc, pw

    @classmethod
    def eliminate_existing(cls, issns):
        for issn in issns:
            for j in models.Journal.find_by_issn(issn):
                j.delete()
        cls.delete_articles_by_issns(issns)

    @staticmethod
    def delete_articles_by_issns(issns):
        # Tombstoning needs the article's owning journal, which by now has been removed (or never existed, for
        # leftovers from an earlier run), so delete without tombstones; they are of no use for testdrive data anyway
        q = ArticleQuery(issns=issns)
        models.Article.delete_selected(query=q.query(), snapshot=False, tombstone=False)

    def teardown(self, params) -> dict:
        for acc in params.get("accounts", {}).values():
            models.Account.remove_by_id(acc["username"])
        self.teardown_journals(params)
        # by ISSN, so articles the tester uploaded during the test are removed along with the seeded one
        upload_data = params.get("upload_data", {})
        issns = [i for i in (upload_data.get("journal_pissn"), upload_data.get("journal_eissn")) if i]
        if issns:
            models.Article.delete_selected(query={"query": {"terms": {"index.issn.exact": issns}}},
                                           snapshot=False, tombstone=False)
        return self.SUCCESS
