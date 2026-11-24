"""
#4343: the bulk article status API and the publisher XML upload page must report the same outcome.

Each scenario runs the shared upload_process on a BulkArticles record, then checks the API response
for it and renders the upload history page from a FileUpload holding the same data.
"""
import json
import os
import tempfile
from unittest.mock import patch

from flask import render_template

from doajtest.fixtures.article_doajxml import DoajXmlArticleFixtureFactory, to_articles
from doajtest.helpers import DoajTestCase
from doajtest.unit_tester.article_upload_tester import create_simple_journal, create_simple_publisher
from portality import models
from portality.core import app
from portality.crosswalks.exceptions import CrosswalkException
from portality.tasks.helpers import articles_upload_helper, background_helper
from portality.ui import templates
from portality.ui.messages import Messages
from portality.util import url_for

OWNER = "testowner"


def valid_articles():
    return (to_articles(DoajXmlArticleFixtureFactory.upload_2_issns_correct())
            + to_articles(DoajXmlArticleFixtureFactory.upload_1_issn_correct()))


def invalid_articles():
    # one ISSN does not match the journal
    return to_articles(DoajXmlArticleFixtureFactory.upload_2_issns_ambiguous())


class TestArticlesUploadStatusSync(DoajTestCase):

    def setUp(self):
        super().setUp()
        self.fix_es_mapping()
        self.acc = create_simple_publisher(OWNER)
        self.acc.add_role("api")
        self.acc.generate_api_key()
        self.acc.save(blocking=True)
        create_simple_journal(OWNER, pissn="1234-5678", eissn="9876-5432", blocking=True)

    def run_upload(self, articles_factory):
        # upload_process moves or deletes the uploaded file, so give it a real one
        tmp = tempfile.mkdtemp()
        path = os.path.join(tmp, "upload.json")
        open(path, "w").close()

        upload = models.BulkArticles(owner=OWNER)
        with patch.dict(app.config, {"FAILED_ARTICLE_DIR": tmp}):
            articles_upload_helper.upload_process(upload, background_helper.create_job(OWNER, '__action__'),
                                                  path, articles_factory)
        upload.save(blocking=True)
        return upload

    def api_status(self, upload):
        with self.app_test.test_client() as t_client:
            resp = t_client.get(url_for('api_v4.bulk_article_create_status',
                                        upload_id=upload.id, api_key=self.acc.api_key))
        assert resp.status_code == 200
        return json.loads(resp.data.decode('utf-8'))

    def ui_notes(self, upload):
        fu = models.FileUpload(**upload.data)
        fu.data.update({"filename": "articles.xml", "schema": "doaj"})
        with self._make_and_push_test_context_manager(acc=self.acc):
            html = render_template(templates.PUBLISHER_XML_UPLOAD, previous=[fu], schema="", error=False)
        return " ".join(html.split())

    def test_all_valid__processed(self):
        upload = self.run_upload(lambda _: valid_articles())

        assert upload.status == "processed"
        assert upload.imported == 2
        assert models.Article.count() == 2

        api = self.api_status(upload)
        assert api["status"] == "processed"
        assert api["results"] == {"imported": 2, "failed": 0, "update": 0, "new": 2}
        assert "error" not in api

        ui = self.ui_notes(upload)
        assert "successfully processed" in ui
        assert "2 articles imported (2 new, 0 updated)" in ui
        assert "Valid articles not imported" not in ui

    def test_mixed_valid_and_invalid__failed_with_counts(self):
        upload = self.run_upload(lambda _: valid_articles() + invalid_articles())

        assert upload.status == "failed"
        assert upload.imported == 0
        assert upload.valid_but_not_imported == 2
        assert upload.failed_imports == 1
        assert models.Article.count() == 0

        api = self.api_status(upload)
        assert api["status"] == "failed"
        assert api["results"] == {"valid_but_not_imported": 2, "failed": 1}
        assert api["error"] == Messages.EXCEPTION_ARTICLE_BATCH_FAIL
        assert api["failure_reasons"] == {"unmatched": ["2345-6789"]}

        ui = self.ui_notes(upload)
        assert "processing failed" in ui
        assert "partial success" not in ui
        assert Messages.EXCEPTION_ARTICLE_BATCH_FAIL in ui
        assert "Valid articles not imported: 2. Failed articles: 1." in ui
        assert "2345-6789" in ui

    def test_all_invalid__failed_with_counts(self):
        upload = self.run_upload(lambda _: invalid_articles())

        assert upload.status == "failed"
        assert upload.valid_but_not_imported == 0
        assert upload.failed_imports == 1
        assert models.Article.count() == 0

        api = self.api_status(upload)
        assert api["status"] == "failed"
        assert api["results"] == {"valid_but_not_imported": 0, "failed": 1}
        assert api["error"] == Messages.EXCEPTION_ARTICLE_BATCH_FAIL

        ui = self.ui_notes(upload)
        assert "processing failed" in ui
        assert "Valid articles not imported: 0. Failed articles: 1." in ui

    def test_unreadable_articles__failed_without_counts(self):
        def bad_factory(_):
            raise CrosswalkException(message="Article at index 0: bad metadata")

        upload = self.run_upload(bad_factory)

        assert upload.status == "failed"
        assert upload.failed_imports == 0
        assert models.Article.count() == 0

        api = self.api_status(upload)
        assert api["status"] == "failed"
        assert "results" not in api
        assert api["error"] == "Article at index 0: bad metadata"

        ui = self.ui_notes(upload)
        assert "processing failed" in ui
        assert "Article at index 0: bad metadata" in ui
        assert "Valid articles not imported" not in ui

    def test_legacy_partial_record__unchanged(self):
        # records written before #4343 can still carry status "partial"
        upload = models.BulkArticles(owner=OWNER)
        upload.failed(Messages.EXCEPTION_ARTICLE_BATCH_FAIL)
        upload.partial(2, 1, 0, 0)
        upload.save(blocking=True)

        api = self.api_status(upload)
        assert api["status"] == "processed_partial"
        assert api["results"]["imported"] == 2
        assert api["results"]["failed"] == 1

        ui = self.ui_notes(upload)
        assert "partial success" in ui
        assert Messages.EXCEPTION_ARTICLE_BATCH_FAIL in ui
