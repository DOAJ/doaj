import tempfile
from pathlib import Path

from flask_login import login_user

from unittest import TestCase
from portality import core, dao
from portality.app import app
from portality.tasks.redis_huey import main_queue, long_running
import dictdiffer
from datetime import datetime
from glob import glob
import os, csv, shutil
from portality.lib import paths
import functools


def patch_config(inst, properties):
    originals = {}
    for k, v in properties.items():
        originals[k] = inst.config.get(k)
        inst.config[k] = v
    return originals


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


CREATED_INDICES = []


def create_index(index_type):
    if index_type in CREATED_INDICES:
        return
    core.initialise_index(app, core.es_connection, only_mappings=[index_type])
    CREATED_INDICES.append(index_type)


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


class DoajTestCase(TestCase):
    app_test = app
    originals = {}

    @classmethod
    def setUpClass(cls) -> None:
        cls.originals = patch_config(app, {
            "STORE_IMPL": "portality.store.StoreLocal",
            "STORE_LOCAL": paths.rel2abs(__file__, "..", "tmp", "store", "main", cls.__name__.lower()),
            "STORE_TMP_DIR": paths.rel2abs(__file__, "..", "tmp", "store", "tmp", cls.__name__.lower()),
            "STORE_CACHE_CONTAINER": "doaj-data-cache-placeholder" + '-' + cls.__name__.lower(),
            "ES_RETRY_HARD_LIMIT": 0,
            "ES_BLOCK_WAIT_OVERRIDE": 0.1,
            "ELASTIC_SEARCH_DB": app.config.get('ELASTIC_SEARCH_TEST_DB'),
            'ELASTIC_SEARCH_DB_PREFIX': core.app.config['ELASTIC_SEARCH_TEST_DB_PREFIX'] + cls.__name__.lower() + '-',
            "FEATURES": app.config['VALID_FEATURES'],
            'ENABLE_EMAIL': False,
            "FAKER_SEED": 1,
            'CMS_BUILD_ASSETS_ON_STARTUP': False
        })

        main_queue.always_eager = True
        long_running.always_eager = True

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
        # time.sleep(1) # I don't know why we slept here, but not in tearDown, so I have removed it

    @classmethod
    def tearDownClass(cls) -> None:
        patch_config(app, cls.originals)
        cls.originals = {}

    def setUp(self):
        pass

    def tearDown(self):
        for f in self.list_today_article_history_files() + self.list_today_journal_history_files():
            os.remove(f)
        shutil.rmtree(paths.rel2abs(__file__, "..", "tmp"), ignore_errors=True)

        self.reset_db_record()

    @staticmethod
    def reset_db_record():
        global CREATED_INDICES
        if len(CREATED_INDICES) > 0:
            dao.DomainObject.destroy_index()
            CREATED_INDICES = []

    def list_today_article_history_files(self):
        return glob(os.path.join(app.config['ARTICLE_HISTORY_DIR'], datetime.now().strftime('%Y-%m-%d'), '*'))

    def list_today_journal_history_files(self):
        return glob(os.path.join(app.config['JOURNAL_HISTORY_DIR'], datetime.now().strftime('%Y-%m-%d'), '*'))

    def _make_and_push_test_context(self, path="/", acc=None):
        ctx = self.app_test.test_request_context(path)
        ctx.push()
        if acc is not None:
            acc.save(blocking=True)
            login_user(acc)

        return ctx


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
    print('Changed :: keys which are the same in {d1} and {d2} but whose values are different'.format(d1=d1_label, d2=d2_label))
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
        print('Unchanged :: keys which are the same in {d1} and {d2} and whose values are also the same'.format(d1=d1_label, d2=d2_label))
        print(differ.unchanged())


def load_from_matrix(filename, test_ids):
    if test_ids is None:
        test_ids = []
    with open(paths.rel2abs(__file__, "matrices", filename), 'r') as f:
        reader = csv.reader(f)
        next(reader)   # pop the header row
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
            _new_path = Path(tempfile.NamedTemporaryFile().name)
            _new_path.mkdir(parents=True, exist_ok=True)
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

