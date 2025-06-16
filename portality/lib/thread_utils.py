import time
from typing import Callable


def wait_until(cond_fn: Callable[[], bool], timeout=10, sleep_time=0.1,
               timeout_msg='fail to meet the condition within the timeout period.', fallthrough: bool = False):
    start = time.time()
    while (time.time() - start) < timeout:
        if cond_fn():
            return
        time.sleep(sleep_time)
    if fallthrough:
        # Skip raising the error if we're willing to risk the condition not being met
        return
    else:
        raise TimeoutError(timeout_msg)
