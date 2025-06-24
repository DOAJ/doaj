import csv
import functools
import hashlib
import logging
import os
import shutil
from contextlib import contextmanager
import time
from glob import glob
from unittest import TestCase
from copy import deepcopy

import dictdiffer
from flask_login import login_user

from doajtest.fixtures import ArticleFixtureFactory, ApplicationFixtureFactory
from portality import core, dao, models
from portality.core import app
from portality.dao import any_pending_tasks, query_data_tasks
from portality.lib import paths, dates
from portality.lib.dates import FMT_DATE_STD
from portality.lib.thread_utils import wait_until
from portality.tasks.redis_huey import events_queue, scheduled_short_queue, scheduled_long_queue
from portality.util import url_for, patch_config


def with_es(_func=None, *, indices=None, warm_mappings=None):
    def with_es_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            obj = WithES(func, indices, warm_mappings)
            return obj.__call__(*args, **kwargs)

        return wrapper

    if _func is None:
        return with_es_decorator
    else:
        return with_es_decorator(_func)


class WithES:

    def __init__(self, func, indices=None, warm_mappings=None):
        self.func = func
        self.indices = indices
        self.warm_mappings = warm_mappings if warm_mappings is not None else []

    def __call__(self, *args, **kwargs):
        self.setUp()
        resp = self.func(*args, **kwargs)
        self.tearDown()
        return resp

    def setUp(self):
        only_mappings = None
        if self.indices is not None and self.indices != "all":
            only_mappings = self.indices
        core.initialise_index(app, core.es_connection, only_mappings=only_mappings)
        for im in self.warm_mappings:
            if im == "article":
                self.warmArticle()
            if im == "article_tombstone":
                self.warmArticleTombstone()
            # add more types if they are necessary

    def tearDown(self):
        dao.DomainObject.destroy_index()

    def warmArticle(self):
        # push an article to initialise the mappings
        from doajtest.fixtures import ArticleFixtureFactory
        from portality.models import Article
        source = ArticleFixtureFactory.make_article_source()
        article = Article(**source)
        article.save(blocking=True)
        article.delete()
        Article.blockdeleted(article.id)

    def warmArticleTombstone(self):
        # push an article to initialise the mappings
        from doajtest.fixtures import ArticleFixtureFactory
        from portality.models import ArticleTombstone
        source = ArticleFixtureFactory.make_article_source()
        article = ArticleTombstone(**source)
        article.save(blocking=True)
        article.delete()
        ArticleTombstone.blockdeleted(article.id)


CREATED_INDICES = []


def initialise_index():
    core.initialise_index(app, core.es_connection)


def create_index(index_type):
    if "," in index_type:
        # this covers a DAO that has multiple index types for searching purposes
        # expressed as a comma separated list
        index_types = index_type.split(",")
    else:
        index_types = [index_type]
    for it in index_types:
        if it in CREATED_INDICES:
            return
        core.initialise_index(app, core.es_connection, only_mappings=[it])
        CREATED_INDICES.append(it)


def dao_proxy(dao_method, type="class"):
    if type == "class":
        @classmethod
        @functools.wraps(dao_method)
        def proxy_method(cls, *args, **kwargs):
            create_index(cls.__type__)
            return dao_method.__func__(cls, *args, **kwargs)

        return proxy_method

    else:
        @functools.wraps(dao_method)
        def proxy_method(self, *args, **kwargs):
            create_index(self.__type__)
            return dao_method(self, *args, **kwargs)

        return proxy_method


def create_es_db_prefix(_cls):
    class_id = hashlib.sha256(_cls.__module__.encode()).hexdigest()[:10]
    db_prefix = (core.app.config['ELASTIC_SEARCH_TEST_DB_PREFIX'] +
                 f'{_cls.__name__.lower()}_{class_id}-')
    return db_prefix


class DoajTestCase(TestCase):
    app_test = app
    originals = {}

    @classmethod
    def create_app_patch(cls):
        return {
            'AUTOCHECK_INCOMING': False,  # old test cases design and depend on work flow of autocheck disabled
            "STORE_IMPL": "portality.store.StoreLocal",
            "STORE_LOCAL_DIR": paths.rel2abs(__file__, "..", "tmp", "store", "main", cls.__name__.lower()),
            "STORE_TMP_DIR": paths.rel2abs(__file__, "..", "tmp", "store", "tmp", cls.__name__.lower()),
            "STORE_CACHE_CONTAINER": "doaj-data-cache-placeholder" + '-' + cls.__name__.lower(),
            "STORE_ANON_DATA_CONTAINER": "doaj-anon-data-placeholder" + '-' + cls.__name__.lower(),
            "STORE_PUBLIC_DATA_DUMP_CONTAINER": "doaj-data-dump-placeholder" + '-' + cls.__name__.lower(),
            "ES_RETRY_HARD_LIMIT": 0,
            "ES_BLOCK_WAIT_OVERRIDE": 0.5,
            "ES_READ_TIMEOUT": '5m',
            'ES_SOCKET_TIMEOUT': 5 * 60,
            "ELASTIC_SEARCH_DB": app.config.get('ELASTIC_SEARCH_TEST_DB'),
            'ELASTIC_SEARCH_DB_PREFIX': create_es_db_prefix(cls),
            "FEATURES": app.config['VALID_FEATURES'],
            'ENABLE_EMAIL': False,
            "FAKER_SEED": 1,
            "EVENT_SEND_FUNCTION": "portality.events.shortcircuit.send_event",
            'CMS_BUILD_ASSETS_ON_STARTUP': False,
            "UR_CONCURRENCY_TIMEOUT": 0,
            'UPLOAD_ASYNC_DIR': paths.create_tmp_path(is_auto_mkdir=True).as_posix(),
            'HUEY_IMMEDIATE': True,
            'HUEY_ASYNC_DELAY': 0,
            "SEAMLESS_JOURNAL_LIKE_SILENT_PRUNE": False,
            'URLSHORT_ALLOWED_SUPERDOMAINS': ['doaj.org', 'localhost', '127.0.0.1']
        }

    @classmethod
    def setUpClass(cls) -> None:
        import portality.app  # noqa, needed to registing routes

        cls.originals = patch_config(app, cls.create_app_patch())

        # some unittest will capture log for testing, therefor log level must be DEBUG
        cls.app_test.logger.setLevel(logging.DEBUG)

        # Run huey jobs straight away
        events_queue.immediate = True
        scheduled_short_queue.immediate = True
        scheduled_long_queue.immediate = True

        dao.DomainObject.save = dao_proxy(dao.DomainObject.save, type="instance")
        dao.DomainObject.delete = dao_proxy(dao.DomainObject.delete, type="instance")
        dao.DomainObject.bulk = dao_proxy(dao.DomainObject.bulk)
        dao.DomainObject.refresh = dao_proxy(dao.DomainObject.refresh)
        dao.DomainObject.pull = dao_proxy(dao.DomainObject.pull)
        dao.DomainObject.pull_by_key = dao_proxy(dao.DomainObject.pull_by_key)
        dao.DomainObject.send_query = dao_proxy(dao.DomainObject.send_query)
        dao.DomainObject.remove_by_id = dao_proxy(dao.DomainObject.remove_by_id)
        dao.DomainObject.delete_by_query = dao_proxy(dao.DomainObject.delete_by_query)
        dao.DomainObject.iterate = dao_proxy(dao.DomainObject.iterate)
        dao.DomainObject.count = dao_proxy(dao.DomainObject.count)

        # if a test on a previous run has totally failed and tearDownClass has not run, then make sure the index is gone first
        dao.DomainObject.destroy_index()

    @classmethod
    def tearDownClass(cls) -> None:
        patch_config(app, cls.originals)
        cls.originals = {}

    def setUp(self):
        pass

    def tearDown(self):
        for f in self.list_today_article_history_files() + self.list_today_journal_history_files():
            try:
                os.remove(f)
            except FileNotFoundError:
                pass  # could be removed by other thread / process
        shutil.rmtree(paths.rel2abs(__file__, "..", "tmp"), ignore_errors=True)

        self.reset_db_record()

    @staticmethod
    def reset_db_record():
        global CREATED_INDICES
        if len(CREATED_INDICES) > 0:
            dao.DomainObject.destroy_index()
            CREATED_INDICES = []

    def list_today_article_history_files(self):
        return glob(os.path.join(app.config['ARTICLE_HISTORY_DIR'], dates.now_str(FMT_DATE_STD), '*'))

    def list_today_journal_history_files(self):
        return glob(os.path.join(app.config['JOURNAL_HISTORY_DIR'], dates.now_str(FMT_DATE_STD), '*'))

    def _make_and_push_test_context(self, path="/", acc=None):
        ctx = self.app_test.test_request_context(path)
        ctx.push()
        if acc is not None:
            acc.save(blocking=True)
            login_user(acc)

        return ctx

    @contextmanager
    def _make_and_push_test_context_manager(self, path="/", acc=None):
        ctx = self._make_and_push_test_context(path=path, acc=acc)
        yield ctx

        ctx.pop()

    @staticmethod
    def fix_es_mapping():
        """
        you need to call this method if you get some errors like:
        ESMappingMissingError - 'reason': 'No mapping found for [field]

        :return:
        """
        for m in [
             models.Article(**ArticleFixtureFactory.make_article_source()),
             models.Application(**ApplicationFixtureFactory.make_application_source()),
        ]:
            m.save(blocking=True)
            m.delete()
        models.Notification().save()


def diff_dicts(d1, d2, d1_label='d1', d2_label='d2', print_unchanged=False):
    """
    Diff two dictionaries - prints changed, added and removed keys and the changed values. DOES NOT DO NESTED DICTS!

    :param d1: First dict - we compare this with d2
    :param d2: Second dict - we compare against this one
    :param d1_label: Will be used instead of "d1" in debugging output to make it more helpful.
    :param d2_label: Will be used instead of "d2" in debugging output to make it more helpful.
    :param print_unchanged: - should we print set of unchanged keys (can be long and useless). Default: False.
    :return: nothing, prints results to STDOUT
    """
    differ = dictdiffer.DictDiffer(d1, d2)
    print('Added :: keys present in {d1} which are not in {d2}'.format(d1=d1_label, d2=d2_label))
    print(differ.added())
    print()
    print('Removed :: keys present in {d2} which are not in {d1}'.format(d1=d1_label, d2=d2_label))
    print(differ.removed())
    print()
    print('Changed :: keys which are the same in {d1} and {d2} but whose values are different'.format(d1=d1_label,
                                                                                                      d2=d2_label))
    print(differ.changed())
    print()

    if differ.changed():
        print('Changed values :: the values of keys which have changed. Format is as follows:')
        print('  Key name:')
        print('    value in {d1}'.format(d1=d1_label))
        print('    value in {d2}'.format(d2=d2_label))
        print()
        for key in differ.changed():
            print(' ', key + ':')
            print('   ', d1[key])
            print('   ', d2[key])
            print()
        print()

    if print_unchanged:
        print('Unchanged :: keys which are the same in {d1} and {d2} and whose values are also the same'.format(
            d1=d1_label, d2=d2_label))
        print(differ.unchanged())

def diff_dicts_recursive(d1, d2, d1_label, d2_label, context=None, sort_functions=None):

    def _normalise(d, context=None):
        if context is None:
            context = "[root]"
        if isinstance(d, dict):
            for k in d.keys():
                if isinstance(d[k], list):
                    if context + "." + k in sort_functions:
                        d[k] = sorted(d[k], key=sort_functions[context + "." + k])
                    else:
                        try:
                            d[k] = sorted(d[k])
                        except TypeError:
                            pass
                elif isinstance(d[k], dict):
                    d[k] = _normalise(d[k], context + "." + k)
        return d

    # we're going to modify the dictionaries, so make sure we're not changing the originals
    d1 = _normalise(deepcopy(d1))
    d2 = _normalise(deepcopy(d2))

    if context is None:
        context = "[root]"

    if not isinstance(d1, dict) or not isinstance(d2, dict):
        if d1 != d2:
            print("#"*(context.count(".") + 1) + " {}".format(context))
            print("{d1} vs {d2}".format(d1=d1, d2=d2))
            print()
        return

    differ = dictdiffer.DictDiffer(d1, d2)
    print("#"*(context.count(".") + 1) + " {}".format(context))
    if differ.added():
        print('Added :: keys present in "{d1}" {ctx} which are not in "{d2}" {ctx}'.format(d1=d1_label, d2=d2_label, ctx=context))
        print(differ.added())
        print()

    if differ.removed():
        print('Removed :: keys present in "{d2}" {ctx} which are not in "{d1}" {ctx}'.format(d1=d1_label, d2=d2_label, ctx=context))
        print(differ.removed())
        print()

    if differ.changed():
        print('Changed :: keys present in "{d1}" {ctx} and "{d2}" {ctx} whose values are different'.format(d1=d1_label,
                                                                                                      d2=d2_label, ctx=context))
        print(differ.changed())
        print()

    if differ.changed():
        for key in differ.changed():
            ctx = context + "." + key if context else key
            if isinstance(d1[key], list) and isinstance(d2[key], list):
                for i in range(len(d1[key])):
                    if len(d2[key]) < i + 1:
                        print("{ctx} - index {i} does not exist in {d2}".format(ctx=ctx, i=i, d2=d2_label))
                    else:
                        diff_dicts_recursive(d1[key][i], d2[key][i], d1_label, d2_label, ctx + "[{}]".format(i), sort_functions=sort_functions)
            else:
                diff_dicts_recursive(d1[key], d2[key], d1_label, d2_label, ctx, sort_functions=sort_functions)

def load_from_matrix(filename, test_ids):
    if test_ids is None:
        test_ids = []
    with open(paths.rel2abs(__file__, "matrices", filename), 'r') as f:
        reader = csv.reader(f)
        next(reader)  # pop the header row
        cases = []
        for row in reader:
            if row[0] in test_ids or len(test_ids) == 0:
                row[0] = "row_id_" + row[0]
                cases.append(tuple(row))
        return cases


def deep_sort(obj):
    """
    Recursively sort list or dict nested lists
    """
    if isinstance(obj, dict):
        _sorted = {}
        for key in sorted(obj):
            _sorted[key] = deep_sort(obj[key])

    elif isinstance(obj, list):
        new_list = []
        for val in obj:
            new_list.append(deep_sort(val))
        _sorted = sorted(new_list)

    else:
        _sorted = obj

    return _sorted


def patch_history_dir(dir_key):
    def _wrapper(fn):

        @functools.wraps(fn)
        def new_fn(*args, **kwargs):
            # define hist_class
            if dir_key == 'ARTICLE_HISTORY_DIR':
                from portality.models import ArticleHistory
                hist_class = ArticleHistory
            elif dir_key == 'JOURNAL_HISTORY_DIR':
                from portality.models import JournalHistory
                hist_class = JournalHistory
            else:
                raise ValueError(f'unknown dir_key [{dir_key}]')

            # setup new path
            org_config_val = DoajTestCase.app_test.config[dir_key]
            org_hist_dir = hist_class.SAVE_BASE_DIRECTORY
            _new_path = paths.create_tmp_path(is_auto_mkdir=True)
            hist_class.SAVE_BASE_DIRECTORY = _new_path.as_posix()
            DoajTestCase.app_test.config[dir_key] = _new_path.as_posix()

            # run fn
            result = fn(*args, **kwargs)

            # reset / cleanup
            shutil.rmtree(_new_path)
            hist_class.SAVE_BASE_DIRECTORY = org_hist_dir
            DoajTestCase.app_test.config[dir_key] = org_config_val

            return result

        return new_fn

    return _wrapper


class StoreLocalPatcher:

    def setUp(self, cur_app):
        """
        change STORE_IMPL to StoreLocal
        make sure STORE_LOCAL_DIR and STORE_TMP_DIR used new tmp dir
        """
        self.org_store_imp = cur_app.config.get("STORE_IMPL")
        self.org_store_tmp_imp = app.config.get("STORE_TMP_IMPL")
        self.org_store_local_dir = cur_app.config["STORE_LOCAL_DIR"]
        self.org_store_tmp_dir = cur_app.config["STORE_TMP_DIR"]

        self.new_store_local_dir = paths.create_tmp_path(is_auto_mkdir=True)
        self.new_store_tmp_dir = paths.create_tmp_path(is_auto_mkdir=True)

        cur_app.config["STORE_IMPL"] = "portality.store.StoreLocal"
        cur_app.config["STORE_LOCAL_DIR"] = self.new_store_local_dir
        cur_app.config["STORE_TMP_DIR"] = self.new_store_tmp_dir

    def tearDown(self, cur_app):
        cur_app.config["STORE_IMPL"] = self.org_store_imp
        cur_app.config["STORE_TMP_IMPL"] = self.org_store_tmp_imp

        shutil.rmtree(self.new_store_local_dir)
        shutil.rmtree(self.new_store_tmp_dir)
        cur_app.config["STORE_LOCAL_DIR"] = self.org_store_local_dir
        cur_app.config["STORE_TMP_DIR"] = self.org_store_tmp_dir


def apply_test_case_config(new_config):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(self, *args, **kwargs):
            # apply new_config
            _app = getattr(self, 'app_test', None)
            originals = None
            if _app:
                originals = patch_config(_app, new_config)

            # run function
            fn(self, *args, **kwargs)

            # restore
            if originals:
                patch_config(_app, originals)

        return wrapper

    return decorator


def assert_expected_dict(test_case: TestCase, target, expected: dict):
    actual = {key: getattr(target, key) for key in expected.keys()}
    test_case.assertDictEqual(actual, expected)


def login(app_client, email, password, follow_redirects=True):
    return app_client.post(url_for('account.login'),
                           data=dict(user=email, password=password),
                           follow_redirects=follow_redirects)


def logout(app_client, follow_redirects=True):
    return app_client.get(url_for('account.logout'), follow_redirects=follow_redirects)


def wait_until_no_es_incomplete_tasks():
    """

    wait until no ES pending tasks and no data tasks is running

    created for make sure model.save() or model.delete() is completed

    if your data still can not be query, try Model.refresh()

    """

    def _cond_fn():
        return not any_pending_tasks() and len(query_data_tasks(timeout='3m')) == 0

    return wait_until(_cond_fn, 10, 0.2)


def wait_unit(exit_cond_fn, timeout=10, check_interval=0.1,
              timeout_msg="wait_unit but exit_cond timeout"):
    start = time.time()
    while (time.time() - start) < timeout:
        if exit_cond_fn():
            return
        time.sleep(check_interval)
    raise TimeoutError(timeout_msg)


def save_all_block_last(model_list):
    model_list = list(model_list)
    if not model_list:
        return model_list

    *model_list, last = model_list
    for model in model_list:
        model.save()
    last.save(blocking=True)

    return model_list
