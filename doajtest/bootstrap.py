import time
from portality import core, dao
from portality.tasks.redis_huey import main_queue

import logging
logging.getLogger("requests").setLevel(logging.WARNING)

def prepare_for_test():
    core.app.config['ELASTIC_SEARCH_DB'] = core.app.config['ELASTIC_SEARCH_TEST_DB']

    # Ensure all features are enabled so we don't fail feature-specific tests
    core.app.config['FEATURES'] = core.app.config['VALID_FEATURES']

    main_queue.always_eager = True

    # if a test on a previous run has totally failed and tearDown has not run, then make sure the index is gone first
    dao.DomainObject.destroy_index()
    time.sleep(1)
