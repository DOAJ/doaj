from copy import deepcopy
from flask_login import login_user

from doajtest.fixtures import AccountFixtureFactory, EditorGroupFixtureFactory, ApplicationFixtureFactory
from doajtest.helpers import DoajTestCase
from portality.util import patch_config
from portality import models
from portality.lib import query_filters
from portality.bll.services.query import Query
from portality.core import app


class TestQueryFilters(DoajTestCase):
    def setUp(self):
        self.q = Query()
        assert self.q.as_dict() == {"track_total_hits": True, "query": {"match_all": {}}}, self.q.as_dict()
        super(TestQueryFilters, self).setUp()

    def tearDown(self):
        super(TestQueryFilters, self).tearDown()

    def _make_and_push_test_context(self, path="/", acc=None):
        ctx = self.app_test.test_request_context(path)
        ctx.push()
        if acc is not None:
            login_user(acc)

        return ctx

    def test_01_only_in_doaj(self):
        newq = query_filters.only_in_doaj(self.q)
        assert newq.as_dict() == {
            "track_total_hits": True,
            'query': {
                'bool': {
                    'filter': [
                        {'term': {'admin.in_doaj': True}}
                    ]
                }
            }
        }, newq.as_dict()

    def test_02_owner(self):
        acc = models.Account(**AccountFixtureFactory.make_publisher_source())
        self._make_and_push_test_context(acc=acc)
        newq = query_filters.owner(self.q)
        assert newq.as_dict() == {
            "track_total_hits": True,
            'query': {
                'bool': {
                    'filter': [{'term': {'admin.owner.exact': acc.id}}]
                }
            }
        }, newq.as_dict()

    def test_03_update_request(self):
        original_config = patch_config(app, {"UPDATE_REQUESTS_SHOW_OLDEST": '2018-05-03'})

        newq = query_filters.update_request(self.q)
        assert newq.as_dict() == {
            "track_total_hits": True,
            'query': {
                'bool': {
                    'filter': [
                        {"range": {"admin.date_applied": {"gte": '2018-05-03'}}},
                        {"term": {"admin.application_type.exact": "update_request"}}
                    ]
                }
            }
        }, newq.as_dict()

        # Tear down
        patch_config(self.app_test, original_config)

    def test_04_associate(self):
        acc = models.Account(**AccountFixtureFactory.make_assed1_source())
        self._make_and_push_test_context(acc=acc)
        newq = query_filters.associate(self.q)
        assert newq.as_dict() == {
            "track_total_hits": True,
            'query': {
                'bool': {
                    'filter': [{'term': {'admin.editor.exact': acc.id}}]
                }
            }
        }, newq.as_dict()

    def test_05_editor(self):
        eg = EditorGroupFixtureFactory.setup_editor_group_with_editors()
        self._make_and_push_test_context(acc=models.Account.pull('eddie'))
        newq = query_filters.editor(self.q)
        assert newq.as_dict() == {
            "track_total_hits": True,
            'query': {
                'bool': {
                    'must': [{'terms': {'admin.editor_group.exact': [eg.name]}}]
                }
            }
        }, newq.as_dict()

    def test_06_public_result_filter(self):
        res = {
            "hits": {
                "hits": [
                    {"_type": "article", "_source": {"admin": {"publisher_record_id": "some_identifier",
                                                               "upload_id": "zyxwvutsrqpo_upload_id"}, "bibjson": {}}},
                    {"_type": "article", "_source": {"admin": {"publisher_record_id": "some_identifier",
                                                               "upload_id": "zyxwvutsrqpo_upload_id"}, "bibjson": {}}},
                    {"_type": "article", "_source": {"admin": {"publisher_record_id": "some_identifier",
                                                               "upload_id": "zyxwvutsrqpo_upload_id"}, "bibjson": {}}}
                ],
                "total": 3
            }
        }

        newres = query_filters.public_result_filter(res)

        assert newres == {
            "hits": {
                "hits": [
                    {"_type": "article", "_source": {"admin": {}, "bibjson": {}}},
                    {"_type": "article", "_source": {"admin": {}, "bibjson": {}}},
                    {"_type": "article", "_source": {"admin": {}, "bibjson": {}}}
                ],
                "total": 3
            }
        }, newres

    def test_07_public_result_filter_unpacked(self):
        res = {
            "admin": {"publisher_record_id": "some_identifier", "upload_id": "zyxwvutsrqpo_upload_id"},
            "bibjson": {}}

        newres = query_filters.public_result_filter(res, unpacked=True)
        assert newres == {"admin": {}, "bibjson": {}}, newres

    def test_08_publisher_result_filter(self):
        apsrc_admin = ApplicationFixtureFactory.make_update_request_source()['admin']
        # Not all of these properties are applicable to applications, but these test objects are not applications:
        # they are made-up admin sections designed solely to test whether the filter lets the right keys through.
        # We just use applications as a base to construct them.
        apsrc_admin['ticked'] = True
        apsrc_admin['in_doaj'] = True
        apsrc_admin['related_applications'] = [1, 2, 3]
        apsrc_admin['current_application'] = 'abcde'

        allowed = ["ticked", "in_doaj", "related_applications", "current_application", "current_journal",
                   "application_status"]
        forbidden = ['notes', 'contact', 'editor_group', 'editor', 'related_journal']

        res = {
            "hits": {
                "hits": [
                    {"_type": "article", "_source": {"admin": deepcopy(apsrc_admin), "bibjson": {}}},
                    {"_type": "article", "_source": {"admin": deepcopy(apsrc_admin), "bibjson": {}}},
                    {"_type": "article", "_source": {"admin": deepcopy(apsrc_admin), "bibjson": {}}}
                ],
                "total": 3
            }
        }

        newres = query_filters.publisher_result_filter(res)

        for n, r in enumerate(newres['hits']['hits']):
            for allowed_k in allowed:
                assert allowed_k in r['_source']['admin'], \
                    '{} key not found in result {}, but it is allowed and should have been left intact by the filter'.format(
                        allowed_k, n)
            for forbidden_k in forbidden:
                assert forbidden_k not in r['_source']['admin'], \
                    '{} key was found in result {}, but it is forbidden and should have been stripped out by the filter'.format(
                        forbidden_k, n)

    def test_09_publisher_result_filter_unpacked(self):
        apsrc_admin = ApplicationFixtureFactory.make_update_request_source()['admin']
        # Not all of these properties are applicable to applications, but these test objects are not applications:
        # they are made-up admin sections designed solely to test whether the filter lets the right keys through.
        # We just use applications as a base to construct them.
        apsrc_admin['ticked'] = True
        apsrc_admin['in_doaj'] = True
        apsrc_admin['related_applications'] = [1, 2, 3]
        apsrc_admin['current_application'] = 'abcde'

        allowed = ["ticked", "in_doaj", "related_applications", "current_application", "current_journal",
                   "application_status"]
        forbidden = ['notes', 'contact', 'editor_group', 'editor', 'related_journal']

        res = {"admin": deepcopy(apsrc_admin), "bibjson": {}}

        newres = query_filters.publisher_result_filter(res, unpacked=True)

        for allowed_k in allowed:
            assert allowed_k in newres['admin'], \
                '{} key not found in result {}, but it is allowed and should have been left intact by the filter'.format(
                    allowed_k, newres)
        for forbidden_k in forbidden:
            assert forbidden_k not in newres['admin'], \
                '{} key was found in result {}, but it is forbidden and should have been stripped out by the filter'.format(
                    forbidden_k, newres)

    def test_10_prune_author_emails(self):
        """Check we don't let publisher emails through the query endpoint"""
        res = {
            "hits": {
                "hits": [
                    {"_type": "article", "_source": {"admin": {"publisher_record_id": "some_identifier",
                                                               "upload_id": "zyxwvutsrqpo_upload_id"}, "bibjson":
                                                         {"author": [{'name': "Janet Author",
                                                                      'email': 'janet@example.com'}]}}},
                    {"_type": "article", "_source": {"admin": {"publisher_record_id": "some_identifier",
                                                               "upload_id": "zyxwvutsrqpo_upload_id"}, "bibjson":
                                                         {"author": [{'name': "Janet Author",
                                                                      'email': 'janet@example.com'},
                                                                     {'name': "Jimmy Author",
                                                                      'email': 'jimmy@example.com'}]}}},
                    {"_type": "article", "_source": {"admin": {"publisher_record_id": "some_identifier",
                                                               "upload_id": "zyxwvutsrqpo_upload_id"}, "bibjson":
                                                         {"author": [{'name': "Janet Author"},
                                                                     {'name': "Jimmy Author"}]}}},
                ],
                "total": 3
            }
        }

        newres = query_filters.prune_author_emails(res)

        assert newres == {
            "hits": {
                "hits": [
                    {"_type": "article", "_source": {"admin": {"publisher_record_id": "some_identifier",
                                                               "upload_id": "zyxwvutsrqpo_upload_id"}, "bibjson":
                                                         {"author": [{'name': "Janet Author"}]}}},
                    {"_type": "article", "_source": {"admin": {"publisher_record_id": "some_identifier",
                                                               "upload_id": "zyxwvutsrqpo_upload_id"}, "bibjson":
                                                         {"author": [{'name': "Janet Author"},
                                                                     {'name': "Jimmy Author"}]}}},
                    {"_type": "article", "_source": {"admin": {"publisher_record_id": "some_identifier",
                                                               "upload_id": "zyxwvutsrqpo_upload_id"}, "bibjson":
                                                         {"author": [{'name': "Janet Author"},
                                                                     {'name': "Jimmy Author"}]}}},
                ],
                "total": 3
            }
        }, newres

    def test_11_prune_author_emails_unpacked(self):
        """Check we don't let publisher emails through the query endpoint"""
        res1 = {
            "admin": {"publisher_record_id": "some_identifier", "upload_id": "zyxwvutsrqpo_upload_id"},
            "bibjson": {"author": [{'name': "Janet Author", 'email': 'janet@example.com'}]}}
        res2 = {
            "admin": {"publisher_record_id": "some_identifier", "upload_id": "zyxwvutsrqpo_upload_id"},
            "bibjson": {"author": [{'name': "Janet Author", 'email': 'janet@example.com'},
                                   {'name': "Jimmy Author", 'email': 'jimmy@example.com'}]}}
        res3 = {
            "admin": {"publisher_record_id": "some_identifier", "upload_id": "zyxwvutsrqpo_upload_id"},
            "bibjson": {"author": [{'name': "Janet Author"}, {'name': "Jimmy Author"}]}}

        newres1 = query_filters.prune_author_emails(res1, unpacked=True)
        expres1 = {
            "admin": {"publisher_record_id": "some_identifier", "upload_id": "zyxwvutsrqpo_upload_id"},
            "bibjson": {"author": [{'name': "Janet Author"}]}}
        assert newres1 == expres1, newres1

        newres2 = query_filters.prune_author_emails(res2, unpacked=True)
        expres2 = {
            "admin": {"publisher_record_id": "some_identifier", "upload_id": "zyxwvutsrqpo_upload_id"},
            "bibjson": {"author": [{'name': "Janet Author"}, {'name': "Jimmy Author"}]}}
        assert newres2 == expres2, newres2

        newres3 = query_filters.prune_author_emails(res3, unpacked=True)
        expres3 = {
            "admin": {"publisher_record_id": "some_identifier", "upload_id": "zyxwvutsrqpo_upload_id"},
            "bibjson": {"author": [{'name': "Janet Author"}, {'name': "Jimmy Author"}]}}
        assert newres3 == expres3, newres3

    def test_12_private_source(self):
        newq = query_filters.private_source(self.q)
        fields = ["admin.application_status", "admin.ticked", "last_updated", "created_date", "id",
                  "bibjson"]
        assert len(newq.as_dict()["_source"]["includes"]) == len(fields), newq.as_dict()
        assert sorted(newq.as_dict()["_source"]["includes"]) == sorted(fields), newq.as_dict()

    def test_13_public_source(self):
        newq = query_filters.public_source(self.q)
        fields = ["admin.ticked", "last_updated", "created_date", "id", "bibjson"]
        assert len(newq.as_dict()["_source"]["includes"]) == len(fields), newq.as_dict()
        assert sorted(newq.as_dict()["_source"]["includes"]) == sorted(fields), newq.as_dict()
