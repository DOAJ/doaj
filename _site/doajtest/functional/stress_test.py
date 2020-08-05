import requests
import json
import sys
import argparse
import logging
import threading
import time
import inspect

# FIXME: in an ideal world, the functional tests would also be wrapped by doaj.helpers.DoajTestCase
from doajtest.bootstrap import prepare_for_test
prepare_for_test()

MAX_REQUESTS_DEFAULT = 10000

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)

def main(argv=sys.argv):
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("host_with_URL_schema")
    parser.add_argument("-m", "--max-requests", type=int, help="Maximum number of requests to send to the host.", default=MAX_REQUESTS_DEFAULT)

    tests = inspect.getmembers(StressTester, predicate=inspect.ismethod)
    tests = [t[0] for t in tests if not t[0].startswith('_')]
    parser.add_argument('-t', '--test',
            help="Pick which test to run, will run all of them by default. Available tests: " + ', '.join(tests),
            default=argparse.SUPPRESS  # don't display default: None on in the help for this argument
    )
    args = parser.parse_args(argv[1:])
    
    host = args.host_with_URL_schema
    host = host.rstrip('/')
    max_requests = args.max_requests

    try:
        test_picked = args.test
    except AttributeError:
        test_picked = None

    if test_picked:
        if test_picked in tests:
            tests = [test_picked]  # override list of tests, that way only the method with this name will be called
        else:
            raise ValueError('The test you want to run does not exist. Valid names are: ' + ', '.join(tests))

    tester = StressTester(host, max_requests)

    thread_list = []
    for test in tests:
        thread_list.append(threading.Thread(target=getattr(tester, test)))

    for thread in thread_list:
        thread.setDaemon(True)
        thread.start()

    # leave the main thread running to catch Ctrl+C
    while threading.active_count() > 0:
        time.sleep(0.1)

class StressTester:
    def __init__(self, host, max_requests):
        self.host = host
        self.max_requests = max_requests

    def _request(self, url, extra_info=''):
        max_ = self.max_requests + 1
        for i in range(1, max_):
            logging.info('{extra_info}Request {0} of {1}'.format(i, max_ - 1, extra_info=extra_info))
            r = requests.get(url)
            logging.debug('  {extra_info}Response: {0}, length: {1}'.format(r.status_code, len(r.text), extra_info=extra_info))
        logging.info('{extra_info}Done! Ctrl+C to exit.'.format(extra_info=extra_info))

    def csv(self):
        url = '{host}/csv'.format(host=self.host)
        self._request(url, extra_info='CSV ')
    
    def query(self):
        url = '{host}/query/journal,article/_search?&callback=jQuery1710994879342848435_1393754644984&source=%7B%22query%22%3A%7B%22match_all%22%3A%7B%7D%7D%2C%22facets%22%3A%7B%22_type%22%3A%7B%22terms%22%3A%7B%22field%22%3A%22_type%22%2C%22size%22%3A110%7D%7D%2C%22index.classification.exact%22%3A%7B%22terms%22%3A%7B%22field%22%3A%22index.classification.exact%22%2C%22size%22%3A110%7D%7D%2C%22index.language.exact%22%3A%7B%22terms%22%3A%7B%22field%22%3A%22index.language.exact%22%2C%22size%22%3A110%7D%7D%2C%22index.country.exact%22%3A%7B%22terms%22%3A%7B%22field%22%3A%22index.country.exact%22%2C%22size%22%3A110%7D%7D%2C%22index.publisher.exact%22%3A%7B%22terms%22%3A%7B%22field%22%3A%22index.publisher.exact%22%2C%22size%22%3A110%7D%7D%2C%22bibjson.provider.exact%22%3A%7B%22terms%22%3A%7B%22field%22%3A%22bibjson.provider.exact%22%2C%22size%22%3A110%7D%7D%2C%22bibjson.author_pays.exact%22%3A%7B%22terms%22%3A%7B%22field%22%3A%22bibjson.author_pays.exact%22%2C%22size%22%3A110%7D%7D%2C%22index.license.exact%22%3A%7B%22terms%22%3A%7B%22field%22%3A%22index.license.exact%22%2C%22size%22%3A110%7D%7D%2C%22bibjson.author.exact%22%3A%7B%22terms%22%3A%7B%22field%22%3A%22bibjson.author.exact%22%2C%22size%22%3A110%7D%7D%2C%22bibjson.year.exact%22%3A%7B%22terms%22%3A%7B%22field%22%3A%22bibjson.year.exact%22%2C%22size%22%3A110%7D%7D%2C%22bibjson.journal.title.exact%22%3A%7B%22terms%22%3A%7B%22field%22%3A%22bibjson.journal.title.exact%22%2C%22size%22%3A110%7D%7D%7D%7D&_=1393754645062'.format(host=self.host)
        self._request(url, extra_info='Query ')

if __name__ == '__main__':
    main()
