import time
from portality import core, dao

def prepare_for_test():
    core.app.config['ELASTIC_SEARCH_DB'] = core.app.config['ELASTIC_SEARCH_TEST_DB']

    # if a test on a previous run has totally failed and tearDown has not run, then make sure the index is gone first
    dao.DomainObject.destroy_index()
    time.sleep(1)
