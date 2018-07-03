import time
from portality import core, dao
from portality.tasks.redis_huey import main_queue, long_running

import logging
logging.getLogger("requests").setLevel(logging.WARNING)


def prepare_for_test():
    core.app.config['ELASTIC_SEARCH_DB'] = core.app.config['ELASTIC_SEARCH_TEST_DB']

    # Ensure all features are enabled so we don't fail feature-specific tests
    core.app.config['FEATURES'] = core.app.config['VALID_FEATURES']

    # Don't contact the configured mail server during tests
    core.app.config['ENABLE_EMAIL'] = False

    main_queue.always_eager = True
    long_running.always_eager = True

    core.app.config['FAKER_SEED'] = 1

    # if a test on a previous run has totally failed and tearDown has not run, then make sure the index is gone first
    dao.DomainObject.destroy_index()
    time.sleep(1)
