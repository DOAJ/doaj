import json

from doajtest.testdrive.factory import TestDrive
from portality import models
from portality.core import app

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


class MultipleAffiliations(TestDrive):
    def setup(self) -> dict:
        publisher, pw = self.publisher_account()
        journal = self.journals_in_doaj(publisher, n=1, block=True)[0]
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

        report = {}
        self.report_accounts([(publisher, pw)], report)
        self.report_journal_ids([journal], report)
        self.report_article_ids([article], report)
        base = app.config.get("BASE_URL")
        report["links"] = {
            "article_page": f"{base}/article/{article.id}",
            "journal_toc": f"{base}/toc/{eissn}",
            "publisher_xml_upload": f"{base}/publisher/uploadfile",
            "publisher_metadata_form": f"{base}/publisher/metadata",
            "api_create_article": f"{base}/api/articles?api_key={publisher.api_key}",
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

    def teardown(self, params) -> dict:
        self.teardown_accounts(params)
        self.teardown_journals(params)
        # by ISSN, so articles the tester uploaded during the test are removed along with the seeded one
        eissn = params.get("upload_data", {}).get("journal_eissn")
        if eissn:
            models.Article.delete_selected(query={"query": {"term": {"index.issn.exact": eissn}}},
                                           snapshot=False, tombstone=False)
        return self.SUCCESS
