import time
from typing import Callable


def wait_until(cond_fn: Callable[[], bool], timeout=10, sleep_time=0.1):
    start_time = time.time()
    while True:
        if cond_fn():
            return True

        if (time.time() - start_time) > timeout:
            return False

        time.sleep(sleep_time)
