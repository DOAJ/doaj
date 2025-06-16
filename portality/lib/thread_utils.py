import time
from typing import Callable, Any


def wait_until(cond_fn: Callable[[], Any], timeout=10, sleep_time=0.1,
               timeout_msg='fail to meet the condition within the timeout period.', fallthrough: bool = False):
    """ Wait until a function supplies a truthy reply. Or until timeout expires """

    start = time.time()
    result = None
    while (time.time() - start) < timeout:
        result = cond_fn()
        if result:
            return result
        time.sleep(sleep_time)
    if fallthrough:
        # Skip raising the error if we're willing to risk the condition not being met
        return result
    else:
        raise TimeoutError(timeout_msg)
